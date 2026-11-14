import React,{useEffect,useRef,useState} from 'react';
import {Pause,Play,VolumeX} from 'lucide-react';

export function VideoBackground({page}:{page:string}){
  const video=useRef<HTMLVideoElement>(null);
  const bridge=useRef<HTMLCanvasElement>(null),bridgeReady=useRef(false);
  const cacheFirstFrame=()=>{
    const v=video.current,c=bridge.current;if(!v||!c||bridgeReady.current)return;
    try{c.width=v.videoWidth;c.height=v.videoHeight;c.getContext('2d')?.drawImage(v,0,0);bridgeReady.current=true;}catch{/* Native playback remains visible if frame capture is unavailable. */}
  };
  useEffect(()=>{
    let frame=0,lastTime=0,wrapped=false;
    const smooth=(x:number)=>{const t=Math.max(0,Math.min(1,x));return t*t*(3-2*t);};
    const tick=()=>{
      const v=video.current,c=bridge.current;
      if(v&&c&&bridgeReady.current&&Number.isFinite(v.duration)&&v.duration>1){
        if(lastTime-v.currentTime>v.duration/2)wrapped=true;
        const fade=Math.min(.85,v.duration*.17),remaining=v.duration-v.currentTime;
        const alpha=remaining<fade?smooth((fade-remaining)/fade):wrapped&&v.currentTime<.35?1-smooth(v.currentTime/.35):0;
        c.style.opacity=String(alpha);lastTime=v.currentTime;
      }
      frame=requestAnimationFrame(tick);
    };
    frame=requestAnimationFrame(tick);return()=>cancelAnimationFrame(frame);
  },[]);
  const [playing,setPlaying]=useState(true),[failed,setFailed]=useState(false);
  const toggle=()=>{
    if(!video.current)return;
    if(video.current.paused)void video.current.play().then(()=>setPlaying(true)).catch(()=>setPlaying(false));
    else{video.current.pause();setPlaying(false);}
  };
  return <>
    <div className={`video-background ${page==='home'?'home-video':'workspace-video'}`} aria-hidden="true">
      <img src="/assets/lunar-fallback.svg" alt="" className="video-fallback"/>
      <video ref={video} autoPlay muted loop playsInline preload="auto" poster="/assets/lunar-fallback.svg"
        onLoadedData={cacheFirstFrame} onPlaying={()=>{setPlaying(true);setFailed(false);cacheFirstFrame();}} onPause={()=>setPlaying(false)} onError={()=>setFailed(true)}
        style={{opacity:1,zIndex:1}} src="/assets/lunar-background.mp4"/>
      <canvas ref={bridge} className="loop-bridge"/>
      <div className="video-overlay" style={{zIndex:3}}/>
    </div>
    <button className="video-control" aria-label={playing?'Pause background video':'Play background video'} onClick={toggle}
      title={failed?'Video unavailable; static fallback shown':playing?'Pause background video':'Play background video'}>
      {playing?<Pause size={11}/>:<Play size={11}/>}<VolumeX size={12}/><span>{failed?'STATIC VIEW':'LUNAR ATMOSPHERE'}</span>
    </button>
  </>;
}
