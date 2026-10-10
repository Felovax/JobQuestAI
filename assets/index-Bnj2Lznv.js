(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const a of document.querySelectorAll('link[rel="modulepreload"]'))n(a);new MutationObserver(a=>{for(const o of a)if(o.type==="childList")for(const c of o.addedNodes)c.tagName==="LINK"&&c.rel==="modulepreload"&&n(c)}).observe(document,{childList:!0,subtree:!0});function r(a){const o={};return a.integrity&&(o.integrity=a.integrity),a.referrerPolicy&&(o.referrerPolicy=a.referrerPolicy),a.crossOrigin==="use-credentials"?o.credentials="include":a.crossOrigin==="anonymous"?o.credentials="omit":o.credentials="same-origin",o}function n(a){if(a.ep)return;a.ep=!0;const o=r(a);fetch(a.href,o)}})();const k="jobquest-marks";function w(){try{return JSON.parse(localStorage.getItem(k)??"{}")}catch{return{}}}function L(e){try{localStorage.setItem(k,JSON.stringify(e))}catch{}}const h="jobquest-cv";function $(){try{return localStorage.getItem(h)??""}catch{return""}}function S(e){try{localStorage.setItem(h,e)}catch{}}function C(e,t){const r=e.description.length<300;return`Hjelp meg å skrive et utkast til jobbsøknad på norsk for stillingen under.

Regler:
- Bruk BARE erfaring, utdanning og ferdigheter som står i CV-en min. Ikke dikt opp noe.
- Koble konkrete ting fra CV-en til kravene i annonsen.
- 250–350 ord, konkret og personlig tone. Unngå floskler som «brennende engasjement».
- Mangler det noe viktig, skriv [FYLL INN: ...] der det trengs.
- Etter søknaden: gi meg 3 ting fra annonsen jeg bør trekke frem i et intervju.

STILLING: ${e.title}
ARBEIDSGIVER: ${e.company||"(ikke oppgitt)"}
STED: ${e.location||"(ikke oppgitt)"}
SØKNADSFRIST: ${e.deadline||"(ikke oppgitt)"}
LENKE: ${e.apply_url}

ANNONSETEKST:
${e.description||"(mangler)"}
${r?`
(Annonseteksten over er kort. Åpne lenken og lim inn hele annonsen her for et bedre utkast.)
`:""}
MIN CV:
${t.trim()||"[Lim inn CV-en din her – eller legg den inn under «Min CV» på JobQuestAI, så kommer den med automatisk]"}
`}async function b(e){try{return await navigator.clipboard.writeText(e),!0}catch{const t=document.createElement("textarea");t.value=e,document.body.appendChild(t),t.select();const r=document.execCommand("copy");return t.remove(),r}}const E=["Bergen","Oslo","Kristiansand","Stavanger"],T=3,A=7,s={data:null,query:"",city:"Alle",source:"Alle",sort:"score",show:"open",marks:w(),expanded:new Set},i=e=>document.querySelector(e);function l(e){const t=document.createElement("div");return t.textContent=e,t.innerHTML}function M(e){return(Date.now()-new Date(e).getTime())/864e5}function v(e){if(!e.deadline_date)return null;const t=new Date(new Date().toISOString().slice(0,10)).getTime();return Math.round((new Date(e.deadline_date).getTime()-t)/864e5)}function N(e){const t=v(e);if(t===null||t>A)return"";const r=t===0?"Frist i dag":t===1?"Frist i morgen":`Frist om ${t} dager`;return`<span class="badge ${t<=2?"urgent":"soon"}">${r}</span>`}function f(e){return new Date(e).toLocaleDateString("no-NO",{day:"numeric",month:"short"})}function I(){const e=s.query.toLowerCase(),t=s.data.jobs.filter(r=>{const n=s.marks[r.id],a=v(r);return!(a!==null&&a<0||s.show==="open"&&n||s.show==="applied"&&n!=="applied"||s.show==="hidden"&&n!=="hidden"||s.city!=="Alle"&&!r.location.toLowerCase().includes(s.city.toLowerCase())||s.source!=="Alle"&&!r.sources.includes(s.source)||e&&!`${r.title} ${r.company} ${r.description}`.toLowerCase().includes(e))});return s.sort==="newest"?t.sort((r,n)=>(n.published||"").localeCompare(r.published||"")):s.sort==="deadline"&&t.sort((r,n)=>(r.deadline_date||"9999").localeCompare(n.deadline_date||"9999")),t}function O(e){const t=s.marks[e.id],r=e.published&&M(e.published)<=T,n=s.expanded.has(e.id),a=e.score>=60?"high":e.score>=40?"mid":"low",o=[e.company,e.location||"Sted ikke oppgitt"].filter(Boolean).map(l).join(" · "),c=[e.published?`Publisert ${f(e.published)}`:"",e.deadline_date?`Frist: ${f(e.deadline_date)}`:e.deadline?`Frist: ${l(e.deadline)}`:""].filter(Boolean).join(" · "),y=e.links.map((d,m)=>`<a class="btn ${m===0?"primary":""}" href="${l(d.url)}" target="_blank" rel="noopener">
        ${m===0?"Les og søk":"Også på"} · ${l(d.source)} ↗</a>`).join("");return`
    <article class="card ${t??""}" data-id="${l(e.id)}">
      <div class="score ${a}" title="Match-score">${e.score}</div>
      <div class="body">
        <h2>${l(e.title)} ${r?'<span class="badge new">Ny</span>':""} ${N(e)}
            ${t==="applied"?'<span class="badge applied">Søkt</span>':""}</h2>
        <p class="meta">${o}</p>
        ${c?`<p class="meta small">${c}</p>`:""}
        ${e.reasons.length?`<ul class="reasons">${e.reasons.map(d=>`<li>${l(d)}</li>`).join("")}</ul>`:""}
        ${e.description?`<button class="link toggle">${n?"Skjul beskrivelse":"Vis beskrivelse"}</button>`:""}
        ${n?`<div class="desc">${l(e.description)}</div>`:""}
        <div class="actions">
          ${y}
          <button class="btn prompt" title="Kopierer en ferdig prompt med annonsen og CV-en din – lim den inn i Claude.ai">Søknadsprompt</button>
          <button class="btn mark" data-mark="applied">${t==="applied"?"Angre søkt":"Merk som søkt"}</button>
          <button class="btn ghost mark" data-mark="hidden">${t==="hidden"?"Vis igjen":"Skjul"}</button>
        </div>
      </div>
    </article>`}function u(){const e=s.data,t=I();i("#count").textContent=`${t.length} stillinger`,i("#list").innerHTML=t.length?t.map(O).join(""):'<p class="empty">Ingen stillinger her. Prøv et annet filter.</p>';const r=["Alle",...new Set(e.jobs.flatMap(n=>n.sources))];i("#sources").innerHTML=r.map(n=>`<button class="chip ${s.source===n?"on":""}" data-source="${l(n)}">${l(n)}</button>`).join(""),i("#cities").innerHTML=["Alle",...E].map(n=>`<button class="chip ${s.city===n?"on":""}" data-city="${n}">${n}</button>`).join(""),document.querySelectorAll("#tabs button").forEach(n=>n.classList.toggle("on",n.dataset.show===s.show))}function D(){const e=s.data,t=new Date(e.updated).toLocaleString("no-NO",{dateStyle:"medium",timeStyle:"short"}),r=e.sources.map(n=>`<span class="${n.ok?"ok":"fail"}" title="${l(n.error??"")}">${l(n.name)}: ${n.ok?n.count:"feilet"}</span>`).join("");i("#footer").innerHTML=`Oppdatert ${t}<div class="status">${r}</div>`}let g=0;function p(e){const t=i("#toast");t.innerHTML=e,t.classList.add("show"),clearTimeout(g),g=window.setTimeout(()=>t.classList.remove("show"),6e3)}async function x(e){const t=s.data.jobs.find(a=>a.id===e);if(!t)return;const r=$();if(!await b(C(t,r))){p("Klarte ikke å kopiere. Prøv en annen nettleser.");return}p('Prompt kopiert! Lim den inn i <a href="https://claude.ai/new" target="_blank" rel="noopener">Claude.ai ↗</a>'+(r.trim()?"":"<br><small>Tips: legg inn CV-en din under «Min CV», så kommer den med automatisk.</small>"))}function V(){const e=i("#cv-dialog"),t=i("#cv-text");i("#cv-open").addEventListener("click",()=>{t.value=$(),e.showModal()}),i("#cv-save").addEventListener("click",()=>{S(t.value),e.close(),p("CV lagret i denne nettleseren.")}),i("#cv-close").addEventListener("click",()=>e.close())}function _(){i("#search").addEventListener("input",e=>{s.query=e.target.value,u()}),i("#sort").addEventListener("change",e=>{s.sort=e.target.value,u()}),document.addEventListener("click",e=>{const t=e.target,r=t.closest(".card"),n=r==null?void 0:r.dataset.id;if(t.dataset.city)s.city=t.dataset.city;else if(t.dataset.source)s.source=t.dataset.source;else if(t.dataset.show)s.show=t.dataset.show;else if(n&&t.classList.contains("toggle"))s.expanded.has(n)?s.expanded.delete(n):s.expanded.add(n);else if(n&&t.classList.contains("prompt")){x(n);return}else if(n&&t.dataset.mark){const a=t.dataset.mark;s.marks[n]===a?delete s.marks[n]:s.marks[n]=a,L(s.marks)}else return;u()})}async function K(){var e;try{const t=await fetch(`./jobs.json?t=${Date.now()}`);s.data=await t.json()}catch{i("#list").innerHTML='<p class="empty">Fant ingen stillinger ennå. Kjør "Oppdater stillinger" under Actions på GitHub.</p>';return}if(!((e=s.data)!=null&&e.jobs)){i("#list").innerHTML='<p class="empty">Ingen data ennå – første kjøring har ikke skjedd.</p>';return}_(),V(),D(),u()}K();
