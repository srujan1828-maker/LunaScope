// Browser storage may outlive a release, or contain incomplete settings.
type RecordValue = Record<string, unknown>;
const record = (value: unknown): RecordValue => value !== null && typeof value === 'object' && !Array.isArray(value) ? value as RecordValue : {};
const number = (value: unknown, fallback: number, min: number, max: number) => typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max ? value : fallback;

export function restoreValue<T>(value:unknown, fallback:T):T {
  if(Array.isArray(fallback))return (Array.isArray(value)?Array.from(new Set(value.filter(v=>typeof v==='string'))):fallback) as T;
  if(typeof fallback==='string')return (typeof value==='string'&&value.length?value:fallback) as T;
  return value as T;
}

export function restoreMission<T extends {start:string;utcTime?:string;days:number;sunlight:number;earth:number;mast:number;margin:number;comms:boolean;terrain:string}>(value:unknown,fallback:T):T {
  const v=record(value);
  const date=typeof v.start==='string'&&/^20(?:2[5-9]|3[0-2])-\d{2}-\d{2}$/.test(v.start)&&Number.isFinite(Date.parse(v.start))&&new Date(v.start).toISOString().slice(0,10)===v.start?v.start:fallback.start;
  const utcTime=typeof v.utcTime==='string'&&/^(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(v.utcTime)?v.utcTime:'00:00:00';
  return {...fallback,start:date,utcTime,days:number(v.days,fallback.days,1,366),sunlight:number(v.sunlight,fallback.sunlight,0,366),earth:number(v.earth,fallback.earth,0,100),mast:number(v.mast,fallback.mast,.5,30),margin:number(v.margin,fallback.margin,0,10),comms:typeof v.comms==='boolean'?v.comms:fallback.comms,terrain:typeof v.terrain==='string'?v.terrain:fallback.terrain};
}

export function restorePower<T extends {enabled:boolean;panel_area_m2:number;panel_efficiency:number;panel_orientation:string;spacecraft_load_w:number;battery_capacity_wh:number;initial_soc_pct:number;reserve_margin_pct:number}>(value:unknown,fallback:T):T {
  const v=record(value);
  return {...fallback,enabled:typeof v.enabled==='boolean'?v.enabled:fallback.enabled,panel_area_m2:number(v.panel_area_m2,fallback.panel_area_m2,.01,10000),panel_efficiency:number(v.panel_efficiency,fallback.panel_efficiency,.001,1),panel_orientation:v.panel_orientation==='fixed_vertical'?'fixed_vertical':'tracking',spacecraft_load_w:number(v.spacecraft_load_w,fallback.spacecraft_load_w,0,1000000),battery_capacity_wh:number(v.battery_capacity_wh,fallback.battery_capacity_wh,.01,100000000),initial_soc_pct:number(v.initial_soc_pct,fallback.initial_soc_pct,0,100),reserve_margin_pct:number(v.reserve_margin_pct,fallback.reserve_margin_pct,0,100),fixed_azimuth_deg:number(v.fixed_azimuth_deg,0,0,360),derating_factor:number(v.derating_factor,.85,.001,1),charge_efficiency:number(v.charge_efficiency,.92,.001,1),discharge_efficiency:number(v.discharge_efficiency,.95,.001,1)};
}
