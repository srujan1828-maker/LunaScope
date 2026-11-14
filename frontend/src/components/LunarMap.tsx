import React,{useState} from 'react';
import {Crosshair,Layers,Minus,Plus,RotateCcw,MapPin} from 'lucide-react';
import {MissionState} from '../mission';

export function LunarMap({state}:{state:MissionState}){
  const [zoom,setZoom]=useState(1),[layer,setLayer]=useState('relief'),[hover,setHover]=useState('');
  const [position,setPosition]=useState({x:0,y:0});
  const project=(lat:number,lon:number)=>{const radius=2*Math.tan(Math.PI/4+lat*Math.PI/360)*1737400/1000;return {x:350+radius*Math.sin(lon*Math.PI/180)*1.45,y:290-radius*Math.cos(lon*Math.PI/180)*1.45};};
  const selected=state.sites.find(s=>s.site_id===state.selected);
  const craters=[{x:350,y:292,r:36,name:'SHACKLETON'},{x:311,y:227,r:43,name:'DE GERLACHE'},{x:345,y:149,r:49,name:'HAWORTH'},{x:445,y:260,r:55,name:'FAUSTINI'},{x:454,y:180,r:38,name:'SHOEMAKER'},{x:427,y:76,r:51,name:'NOBILE'},{x:256,y:387,r:45,name:''},{x:548,y:341,r:65,name:''},{x:164,y:170,r:58,name:''},{x:199,y:456,r:65,name:''}];
  return <div className="lunar-map panel">
    <div className="panel-heading"><div><span className="eyebrow">EXPLORATION ATLAS</span><h3>Lunar south pole</h3></div><label className="map-layer"><Layers size={14}/><select aria-label="Map layer" value={layer} onChange={e=>setLayer(e.target.value)}><option value="relief">Illustrative relief</option><option value="sites">Sites & coordinates</option></select></label></div>
    <div className="map-canvas" onPointerMove={e=>{const box=e.currentTarget.getBoundingClientRect();setPosition({x:Math.round((e.clientX-box.left)/box.width*700),y:Math.round((e.clientY-box.top)/box.height*580)});}}>
      <svg viewBox="0 0 700 580" role="img" aria-label="Interactive south polar site map. Relief is illustrative; markers use demonstration catalog coordinates.">
        <defs><radialGradient id="ground"><stop stopColor="#42454a"/><stop offset="1" stopColor="#101722"/></radialGradient><radialGradient id="crater"><stop stopColor="#0b1018"/><stop offset=".72" stopColor="#1c232c"/><stop offset=".88" stopColor="#62666a"/><stop offset=".94" stopColor="#252c35"/><stop offset="1" stopColor="#353b43"/></radialGradient>
          <filter id="terrain-grain"><feTurbulence type="fractalNoise" baseFrequency=".07" numOctaves="4" seed="17"/><feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="linear" slope=".14"/></feComponentTransfer><feBlend in="SourceGraphic" mode="overlay"/></filter></defs>
        <rect width="700" height="580" fill="#101722"/>
        <g transform={`translate(350 290) scale(${zoom}) translate(-350 -290)`}>
          <rect width="700" height="580" fill="url(#ground)"/>
          {layer==='relief'&&<g filter="url(#terrain-grain)">{craters.map((c,i)=><g key={i}><circle cx={c.x} cy={c.y} r={c.r} fill="url(#crater)"/><circle cx={c.x-c.r*.12} cy={c.y-c.r*.08} r={c.r*.83} fill="none" stroke="#828589" strokeOpacity=".16"/>{c.name&&<text x={c.x} y={c.y+c.r+14} textAnchor="middle" fill="#c2c6cd" fontSize="8" letterSpacing="2">{c.name}</text>}</g>)}</g>}
          <g fill="none" stroke="#d0d6df" strokeOpacity=".12" strokeWidth=".7">{[75,150,225].map(r=><circle key={r} cx="350" cy="290" r={r}/>)}{[0,45,90,135].map(a=><path key={a} transform={`rotate(${a} 350 290)`} d="M50 290H650"/>)}</g>
          <g stroke="#d8b36a" strokeWidth="1" opacity=".7"><path d="M339 290h22M350 279v22"/></g><text x="365" y="297" fill="#d8b36a" fontSize="9">90°S</text>
          {state.sites.map((s,i)=>{const p=project(s.lat_deg,s.lon_deg);const color=s.site_id===state.primary?'#d8b36a':state.backups.includes(s.site_id)?(state.rank(s.site_id)?.passed?'#84c99d':'#e06c68'):'#63c9c0';return <g key={s.site_id} role="button" tabIndex={0} aria-label={`Select ${s.name}`} onClick={()=>state.setSelected(s.site_id)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();state.setSelected(s.site_id);}}} onMouseEnter={()=>setHover(s.name)} onMouseLeave={()=>setHover('')} style={{cursor:'pointer'}}>
            <title>{s.name} · {s.lat_deg.toFixed(2)}°, {s.lon_deg.toFixed(2)}°</title><circle cx={p.x} cy={p.y} r="18" fill={color} opacity=".08"/>{s.site_id===state.selected&&<circle cx={p.x} cy={p.y} r="12" fill="none" stroke={color} strokeWidth="1"/>}<circle cx={p.x} cy={p.y} r="5" fill={color} stroke="#101722" strokeWidth="2"/><text x={p.x+10} y={p.y-9+(i%2)*20} fontSize="8" fill={color}>{String(i+1).padStart(2,'0')}</text></g>;})}
        </g>
        <text x="28" y="30" fill="#8995a5" fontSize="9" letterSpacing="2">SOUTH POLAR STEREOGRAPHIC</text><text x="28" y="552" fill="#8995a5" fontSize="8">ILLUSTRATIVE RELIEF · NOT A LOLA ELEVATION MAP</text>
        <path d="M595 532h70m-70-4v8m70-8v8" stroke="#8995a5"/><text x="629" y="524" textAnchor="middle" fill="#8995a5" fontSize="8">~48 km / {zoom.toFixed(1)}×</text>
      </svg>
      <div className="zoom-controls"><button aria-label="Zoom in" onClick={()=>setZoom(z=>Math.min(3,z+.25))}><Plus size={16}/></button><button aria-label="Zoom out" onClick={()=>setZoom(z=>Math.max(.75,z-.25))}><Minus size={16}/></button><button aria-label="Reset map" onClick={()=>setZoom(1)}><RotateCcw size={15}/></button></div>
      {hover&&<div className="map-hover">{hover}</div>}
      <div className="map-selected"><MapPin size={14}/><div><span>SELECTED LOCATION</span><strong>{selected?.name||'Select a site'}</strong></div><Crosshair size={17}/></div>
    </div>
    <div className="map-foot"><div><span className="legend-dot gold"/>Primary <span className="legend-dot teal"/>Candidate <span className="legend-dot green"/>Passing backup <span className="legend-dot red"/>Failing backup</div><span>{selected ? Math.abs(selected.lat_deg).toFixed(2) : "—"}°S / {selected?.lon_deg.toFixed(2)}°E <small title="Cursor position in schematic pixels">· {position.x},{position.y}</small></span></div>
  </div>;
}
