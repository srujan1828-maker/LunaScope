import {EvaluatedSiteData} from '../types';
export function SolarElevationDistribution({data}:{data?:EvaluatedSiteData}){
 if(!data)return <p className="integration-empty">Waiting for solar geometry…</p>;
 const values=data.ephemeris.sun_elevation,lo=Math.min(...values),hi=Math.max(...values),span=Math.max(.01,hi-lo),bins=Array(12).fill(0);
 // Weight by elapsed duration because event refinement creates irregular samples.
 for(let i=0;i<values.length-1;i++)bins[Math.min(11,Math.floor((values[i]-lo)/span*12))]+=data.timestamps[i+1]-data.timestamps[i];
 const total=bins.reduce((a,b)=>a+b,0)||1,max=Math.max(...bins,1);
 return <div className="solar-elevation-chart"><svg viewBox="0 0 340 150" role="img" aria-label="Time-weighted solar elevation distribution">{bins.map((v,i)=><rect key={i} x={35+i*23} y={112-v/max*90} width="20" height={v/max*90} fill="#dfa76a" opacity=".8"><title>{(lo+i*span/12).toFixed(2)}° to {(lo+(i+1)*span/12).toFixed(2)}°: {(v/total*100).toFixed(1)}% of mission</title></rect>)}<text x="35" y="135" fill="#94a3b8" fontSize="11">{lo.toFixed(2)}°</text><text x="310" y="135" fill="#94a3b8" fontSize="11" textAnchor="end">{hi.toFixed(2)}°</text></svg><small>Duration weighted · mission window</small></div>;
}
