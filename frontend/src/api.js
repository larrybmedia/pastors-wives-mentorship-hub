const BASE=import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000/api'
export function token(){return localStorage.getItem('hub_token')}
export async function api(path,options={}){
 const headers={'Content-Type':'application/json',...(options.headers||{})}
 if(token()) headers.Authorization=`Bearer ${token()}`
 const res=await fetch(`${BASE}${path}`,{...options,headers})
 const data=await res.json().catch(()=>({error:'Unexpected server response'}))
 if(!res.ok) throw new Error(data.error||data.message||'Request failed')
 return data
}
