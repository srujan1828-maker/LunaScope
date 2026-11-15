import {useEffect,useRef,useState} from 'react';
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import type {SurfaceFrame} from './surfaceTypes';

// Globe axes: longitude 0 = +X, east = -Z, north = +Y.
const location=(lat:number,lon:number)=>{const p=lat*Math.PI/180,l=lon*Math.PI/180;return new THREE.Vector3(Math.cos(p)*Math.cos(l),Math.sin(p),-Math.cos(p)*Math.sin(l));};
export function MoonGlobe({frame,lat,lon}:{frame:SurfaceFrame|null;lat:number;lon:number}){
  const host=useRef<HTMLDivElement>(null),runtime=useRef<any>(null);
  const [error,setError]=useState(''),[ready,setReady]=useState(false);
  useEffect(()=>{
    if(!host.current)return;const node=host.current;let active=true,animation=0;let renderer:THREE.WebGLRenderer;
    try{renderer=new THREE.WebGLRenderer({antialias:true});}catch{setError('WebGL is unavailable. Open the local surface view for its numerical analysis.');return;}
    renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;
    renderer.domElement.setAttribute('aria-label','Complete 3D Moon globe with NASA LRO imagery');node.appendChild(renderer.domElement);
    const scene=new THREE.Scene();scene.background=new THREE.Color('#02040a');
    const camera=new THREE.PerspectiveCamera(40,1,.01,50);camera.position.set(3.3,-1.5,1.6);
    const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.enablePan=false;controls.minDistance=1.2;controls.maxDistance=7;
    const fill=new THREE.AmbientLight(0xffffff,.6);scene.add(fill);
    const light=new THREE.DirectionalLight(0xfff6e6,2.5);light.position.set(4,2,3);scene.add(light);
    const material=new THREE.MeshStandardMaterial({color:0xffffff,roughness:1});
    const moon=new THREE.Mesh(new THREE.SphereGeometry(1,256,128),material);scene.add(moon);
    const marker=new THREE.Mesh(new THREE.SphereGeometry(.012,16,12),new THREE.MeshBasicMaterial({color:0x65e4d1}));scene.add(marker);
    const ring=new THREE.Mesh(new THREE.RingGeometry(.018,.024,48),new THREE.MeshBasicMaterial({color:0x65e4d1,side:THREE.DoubleSide}));scene.add(ring);
    runtime.current={camera,controls,moon,marker,ring,light,dirty:true};controls.addEventListener('change',()=>{if(runtime.current)runtime.current.dirty=true;});
    new THREE.TextureLoader().load('/assets/lroc_color_2k.jpg',texture=>{if(!active){texture.dispose();return;}texture.colorSpace=THREE.SRGBColorSpace;texture.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());material.map=texture;material.needsUpdate=true;runtime.current.dirty=true;setReady(true);},undefined,()=>{if(active)setError('NASA globe imagery could not load. Check the globe asset installation.');});
    new THREE.TextureLoader().load('/assets/moon-global-bump.png',texture=>{if(!active){texture.dispose();return;}material.bumpMap=texture;material.bumpScale=19.3825/1737.4;material.needsUpdate=true;runtime.current.dirty=true;});
    fetch('/assets/moon-global-height.json').then(r=>{if(!r.ok)throw new Error();return r.json();}).then(data=>{
      if(!active)return;const geometry=moon.geometry,position=geometry.attributes.position,uv=geometry.attributes.uv;
      for(let i=0;i<position.count;i++){
        const x=Math.min(data.width-1,Math.floor((uv.getX(i)%1)*data.width)),y=Math.min(data.height-1,Math.floor((1-uv.getY(i))*data.height));
        const elevation=(uv.getY(i)===0||uv.getY(i)===1)?data.heights_km.slice(y*data.width,(y+1)*data.width).reduce((a:number,b:number)=>a+b,0)/data.width:data.heights_km[y*data.width+x];if(!Number.isFinite(elevation))continue;
        const v=new THREE.Vector3().fromBufferAttribute(position,i).normalize().multiplyScalar(1+elevation/1737.4);position.setXYZ(i,v.x,v.y,v.z);
      }position.needsUpdate=true;geometry.computeVertexNormals();geometry.computeBoundingSphere();runtime.current.dirty=true;
    }).catch(()=>{if(active)setError('Global elevation overview unavailable; the globe uses a reference sphere. Local terrain analysis is separate.');});
    const resize=new ResizeObserver(()=>{const w=node.clientWidth,h=node.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();if(runtime.current)runtime.current.dirty=true;});resize.observe(node);
    const draw=()=>{controls.update();if(runtime.current?.dirty){renderer.render(scene,camera);runtime.current.dirty=false;}animation=requestAnimationFrame(draw);};draw();
    return()=>{active=false;cancelAnimationFrame(animation);resize.disconnect();controls.dispose();material.map?.dispose();material.bumpMap?.dispose();scene.traverse(o=>{const m=o as THREE.Mesh;m.geometry?.dispose();if(m.material&&!Array.isArray(m.material))m.material.dispose();});renderer.dispose();renderer.forceContextLoss();node.removeChild(renderer.domElement);runtime.current=null;};
  },[]);
  useEffect(()=>{
    const r=runtime.current;if(!r)return;const up=location(lat,lon);r.marker.position.copy(up).multiplyScalar(1.015);r.ring.position.copy(up).multiplyScalar(1.014);r.ring.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1),up);
    if(frame){const p=lat*Math.PI/180,l=lon*Math.PI/180;const east=new THREE.Vector3(-Math.sin(l),0,-Math.cos(l)),north=new THREE.Vector3(-Math.sin(p)*Math.cos(l),Math.cos(p),Math.sin(p)*Math.sin(l));const d=frame.sun.direction_scene;r.light.position.copy(east.multiplyScalar(d[0]).add(up.clone().multiplyScalar(d[1])).add(north.multiplyScalar(-d[2])).multiplyScalar(5));}
    r.dirty=true;
  },[frame,lat,lon]);
  const focus=(pole:boolean)=>{const r=runtime.current;if(!r)return;r.camera.position.copy(pole?location(lat,lon).multiplyScalar(3.7):new THREE.Vector3(3.3,-1.5,1.6));r.controls.target.set(0,0,0);r.controls.update();r.dirty=true;};
  return <><div ref={host} className="terrain-viewport" data-testid="moon-globe"/><div className="globe-caption"><span className="eyebrow">COMPLETE MOON / NASA LRO</span><strong>{ready?'LROC color mosaic + LOLA global shape':'Loading NASA Moon imagery…'}</strong><span>Drag to rotate · scroll to zoom · teal marker: selected location</span>{error&&<span role="alert">{error}</span>}</div><div className="globe-controls"><button className="button secondary compact" onClick={()=>focus(false)}>Reset globe</button><button className="button primary compact" onClick={()=>focus(true)}>Focus selected location</button></div></>;
}
