import {useEffect,useRef,useState} from 'react';
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import type {SurfaceFrame,TerrainCrop,PickedPoint} from './surfaceTypes';

type Props={mesh:TerrainCrop|null;frame:SurfaceFrame|null;onPick:(point:PickedPoint)=>void;view:'orbit'|'ground'|'sun'|'earth';colored:boolean;inspectionLight:boolean};
export function TerrainViewport({mesh,frame,onPick,view,colored,inspectionLight}:Props){
  const host=useRef<HTMLDivElement>(null),runtime=useRef<any>(null),latest=useRef({mesh,frame,onPick});
  latest.current={mesh,frame,onPick};
  const [failure,setFailure]=useState('');
  useEffect(()=>{
    if(!host.current)return;const element=host.current;let renderer:THREE.WebGLRenderer;
    try{renderer=new THREE.WebGLRenderer({antialias:true,logarithmicDepthBuffer:true,powerPreference:'high-performance'});}catch{setFailure('3D graphics are unavailable in this browser. Numerical readings and the measured horizon remain available.');return;}
    renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
    renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.3;
    renderer.domElement.setAttribute('aria-label','Interactive NASA elevation terrain: drag to orbit, wheel to zoom, shift-drag to pan, click to inspect');
    renderer.domElement.setAttribute('role','img');element.appendChild(renderer.domElement);
    const scene=new THREE.Scene();scene.background=new THREE.Color('#03060b');
    const camera=new THREE.PerspectiveCamera(48,1,.0001,1e7);camera.position.set(4,3,5);
    const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.minDistance=.0005;controls.maxDistance=150;
    const fill=new THREE.AmbientLight(0xa1adc7,.7);scene.add(fill);
    const sunlight=new THREE.DirectionalLight(0xfff3d6,3);sunlight.castShadow=true;sunlight.shadow.mapSize.set(2048,2048);
    sunlight.shadow.camera.near=.1;sunlight.shadow.camera.far=150;sunlight.shadow.normalBias=.002;sunlight.shadow.bias=-.00001;
    scene.add(sunlight);scene.add(sunlight.target);
    const terrain=new THREE.Mesh(new THREE.BufferGeometry(),new THREE.MeshStandardMaterial({color:0xa5a5a2,roughness:1,metalness:0,side:THREE.DoubleSide}));
    terrain.receiveShadow=true;terrain.castShadow=true;scene.add(terrain);
    const sun=new THREE.Mesh(new THREE.SphereGeometry(1,24,16),new THREE.MeshBasicMaterial({color:0xfff1bd}));scene.add(sun);
    const earth=new THREE.Mesh(new THREE.SphereGeometry(1,48,32),new THREE.MeshStandardMaterial({color:0x4b93c8,roughness:1}));scene.add(earth);
    const observer=new THREE.Mesh(new THREE.SphereGeometry(.03,12,8),new THREE.MeshBasicMaterial({color:0x63c9c0}));scene.add(observer);
    const axes=new THREE.Group();scene.add(axes);
    const ray=new THREE.Raycaster(),pointer=new THREE.Vector2();let down={x:0,y:0};
    const press=(e:PointerEvent)=>{down={x:e.clientX,y:e.clientY};};
    const pick=(e:PointerEvent)=>{
      if(Math.hypot(e.clientX-down.x,e.clientY-down.y)>5)return;
      const rect=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);
      ray.setFromCamera(pointer,camera);const hit=ray.intersectObject(terrain)[0];const data=latest.current.mesh;
      if(!hit?.face||!data)return;
      const indices=[hit.face.a,hit.face.b,hit.face.c];indices.sort((a,b)=>new THREE.Vector3(...(data.vertices_km[a] as [number,number,number])).distanceTo(hit.point)-new THREE.Vector3(...(data.vertices_km[b] as [number,number,number])).distanceTo(hit.point));
      const i=indices[0];latest.current.onPick({lat_deg:data.latitudes[i],lon_deg:data.longitudes[i],elevation_m:data.elevations_m[i]!,uncertainty_m:data.uncertainty_m[i]});
    };
    renderer.domElement.addEventListener('pointerdown',press);renderer.domElement.addEventListener('pointerup',pick);
    const resize=new ResizeObserver(()=>{const w=element.clientWidth,h=element.clientHeight;if(!w||!h)return;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();if(runtime.current)runtime.current.dirty=true;});resize.observe(element);
    runtime.current={renderer,scene,camera,controls,terrain,sunlight,sun,earth,observer,axes,fill,dirty:true};
    controls.addEventListener('change',()=>{if(runtime.current)runtime.current.dirty=true;});
    let animation=0;
    const draw=()=>{
      controls.update();if(!runtime.current?.dirty){animation=requestAnimationFrame(draw);return;}const current=latest.current.frame;
      if(current){
        const distance=10000;
        for(const [object,body] of [[sun,current.sun],[earth,current.earth]] as const){
          object.position.copy(camera.position).add(new THREE.Vector3(...body.direction_scene).multiplyScalar(distance));
          object.scale.setScalar(Math.tan(body.angular_radius_deg*Math.PI/180)*distance);
        }
      }
      renderer.render(scene,camera);runtime.current.dirty=false;animation=requestAnimationFrame(draw);
    };draw();
    return()=>{cancelAnimationFrame(animation);resize.disconnect();controls.dispose();renderer.domElement.removeEventListener('pointerdown',press);renderer.domElement.removeEventListener('pointerup',pick);
      scene.traverse(o=>{const m=o as THREE.Mesh;m.geometry?.dispose();const mats=Array.isArray(m.material)?m.material:[m.material];mats.forEach(mat=>mat?.dispose());});
      sunlight.shadow.map?.dispose();renderer.dispose();renderer.forceContextLoss();element.removeChild(renderer.domElement);runtime.current=null;};
  },[]);
  useEffect(()=>{
    const r=runtime.current;if(!r||!mesh)return;
    const positions=new Float32Array(mesh.vertices_km.length*3),colors=new Float32Array(positions.length);
    const low=mesh.elevation_range_m[0]??0,high=mesh.elevation_range_m[1]??1;
    mesh.vertices_km.forEach((p,i)=>{positions.set(p.map(v=>v??0),i*3);const c=new THREE.Color().setHSL(.56-(Math.max(0,Math.min(1,((mesh.elevations_m[i]??low)-low)/(high-low||1))))*.45,.34,.44);colors.set([c.r,c.g,c.b],i*3);});
    const indices:number[]=[];const n=mesh.samples;
    for(let y=0;y<n-1;y++)for(let x=0;x<n-1;x++){
      const a=y*n+x,b=a+1,c=a+n,d=c+1;
      if([a,c,b].every(i=>mesh.elevations_m[i]!==null))indices.push(a,c,b);
      if([b,c,d].every(i=>mesh.elevations_m[i]!==null))indices.push(b,c,d);
    }
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.BufferAttribute(positions,3));geometry.setAttribute('color',new THREE.BufferAttribute(colors,3));geometry.setIndex(indices);geometry.computeVertexNormals();
    r.terrain.geometry.dispose();r.terrain.geometry=geometry;
    const half=mesh.width_km*.8;r.sunlight.shadow.camera.left=-half;r.sunlight.shadow.camera.right=half;r.sunlight.shadow.camera.top=half;r.sunlight.shadow.camera.bottom=-half;r.sunlight.shadow.camera.updateProjectionMatrix();
    r.observer.scale.setScalar(Math.max(.1,mesh.width_km/12));
    r.axes.traverse((o:THREE.Object3D)=>{const m=o as THREE.Mesh;m.geometry?.dispose();if(m.material&&!Array.isArray(m.material))m.material.dispose();});r.axes.clear();const length=mesh.width_km*.22;
    for(const [direction,color] of [[new THREE.Vector3(0,0,-1),0x63c9c0],[new THREE.Vector3(1,0,0),0xd8b36a]] as const)r.axes.add(new THREE.ArrowHelper(direction,new THREE.Vector3(0,.02,0),length,color,length*.05,length*.03));
    r.camera.position.set(mesh.width_km*.42,mesh.width_km*.30,mesh.width_km*.5);r.controls.target.set(0,0,0);r.controls.update();
    r.dirty=true;
  },[mesh]);
  useEffect(()=>{const r=runtime.current;if(!r)return;r.sunlight.intensity=frame?3:0;r.sun.visible=!!frame;r.earth.visible=!!frame;if(frame){r.sunlight.position.copy(new THREE.Vector3(...frame.sun.direction_scene).multiplyScalar(55));r.observer.position.y=frame.location.mast_height_m/1000;}r.dirty=true;},[frame,mesh]);
  useEffect(()=>{const r=runtime.current;if(!r)return;r.terrain.material.vertexColors=colored;r.terrain.material.color.set(colored?0xffffff:0xa5a5a2);r.terrain.material.needsUpdate=true;r.dirty=true;},[colored,mesh]);
  useEffect(()=>{const r=runtime.current;if(!r)return;r.fill.intensity=inspectionLight?.7:0;r.dirty=true;},[inspectionLight]);
  useEffect(()=>{
    const r=runtime.current;if(!r||!mesh)return;
    if(view==='orbit'){r.camera.position.set(mesh.width_km*.42,mesh.width_km*.30,mesh.width_km*.5);r.controls.target.set(0,0,0);}
    else {r.camera.position.set(0,(latest.current.frame?.location.mast_height_m??2)/1000,0);const body=view==='earth'?latest.current.frame?.earth:view==='sun'?latest.current.frame?.sun:null;
      r.controls.target.copy(r.camera.position).add(body?new THREE.Vector3(...body.direction_scene).multiplyScalar(10):new THREE.Vector3(0,.02,-10));}
    r.controls.update();
  },[view,mesh]);
  return <div ref={host} className="terrain-viewport" data-testid="terrain-viewport">{failure&&<p className="empty-state" role="alert">{failure}</p>}</div>;
}
