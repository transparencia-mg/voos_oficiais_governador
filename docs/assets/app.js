// app.js - dashboard estático
const FILES_JSON = "files.json"; // lista de CSVs em docs/data/normalized/
let rawRows = [];   // cada linha = um passageiro (original)
let df_voos = [];   // voos agrupados por DB

// util: fetch files.json
async function fetchFilesList(){
  const res = await fetch(FILES_JSON);
  if(!res.ok) throw new Error("Não encontrou files.json");
  return res.json();
}

// util: fetch and parse CSV via PapaParse (auto delimiter)
function fetchCSV(path){
  return new Promise((resolve,reject)=>{
    Papa.parse(path, {
      download: true, header: true, skipEmptyLines: true,
      dynamicTyping: false,
      complete: (res)=> resolve(res.data),
      error: (err)=> reject(err)
    });
  });
}

// Normalize column names (map from your CSV to expected)
function normalizeRow(r){
  // map column keys to normalized keys
  const map = {};
  for(let k in r){
    let k2 = k.trim()
      .replace(/\s+/g,"_")
      .normalize("NFD").replace(/[\u0300-\u036f]/g,""); // remove accents
    map[k2] = r[k];
  }
  return {
    Data: map["Data"] || map["data"] || map["DATA"] || "",
    Diario_de_Bordo: map["Numero_DB"] || map["NumeroDB"] || map["Numero_DB"] || map["Número_DB"] || map["Diario_de_Bordo"] || "",
    Origem: map["Origem"] || "",
    Destino: map["Destino"] || "",
    Horas_Voadas: (map["Horas_Voadas"] || map["HorasVoadas"] || map["Horas Voadas"] || "").toString().replace(",","."),
    Aeronave: map["Aeronave"] || "",
    Orgao: map["Orgao"] || map["Orgao1"] || map["Orgao"] || "",
    Situacao: map["Historico"] || map["Situacao"] || "",
    Passageiros: map["Nome"] || ""
  };
}

// group into flights (one row per DB)
function computeVoos(rows){
  const keyfn = r => `${r.Data}||${r.Diario_de_Bordo}||${r.Origem}||${r.Destino}||${r.Horas_Voadas}||${r.Aeronave}||${r.Orgao}`;
  const map = {};
  rows.forEach(r=>{
    const k = keyfn(r);
    if(!map[k]) map[k] = { ...r, Total_Passageiros:0, Passageiros_List: [] };
    map[k].Total_Passageiros += 1;
    if(r.Passageiros && r.Passageiros.trim()) map[k].Passageiros_List.push(r.Passageiros.trim());
  });
  return Object.values(map);
}

// render summary cards
function renderSummary(dfAll, dfVoos){
  document.getElementById("card-voos").innerText = dfVoos.length;
  const totalHoras = dfVoos.reduce((s,r)=> s + (parseFloat(r.Horas_Voadas)||0), 0);
  document.getElementById("card-horas").innerText = totalHoras.toFixed(1) + "h";
  const totalPass = dfAll.length;
  document.getElementById("card-pass").innerText = totalPass;
  document.getElementById("card-destinos").innerText = new Set(dfVoos.map(d=>d.Destino)).size;
}

// build selects
function buildFilters(dfAll, dfVoos){
  const by = (arr,fn)=> Array.from(new Set(arr.map(fn).filter(x=>x))).sort();
  const anos = by(dfAll, r => (r.Data && r.Data.slice(-4)) || r.Ano || "");
  const origem = by(dfAll, r => r.Origem);
  const destino = by(dfAll, r => r.Destino);
  const orgao = by(dfAll, r => r.Orgao);

  const sel = (id, values, prefix="")=>{
    const s = document.getElementById(id);
    s.innerHTML = `<option value="all">${prefix || "Todos"}</option>` + values.map(v=>`<option value="${v}">${v}</option>`).join("");
  };
  sel("filter-ano", anos, "Ano");
  sel("filter-origem", origem, "Origem");
  sel("filter-destino", destino, "Destino");
  sel("filter-orgao", orgao, "Órgão");
}

// draw destinos bar (top 12)
function drawDestinos(dfVoos){
  const counts = {};
  dfVoos.forEach(r=> counts[r.Destino] = (counts[r.Destino]||0)+1);
  const items = Object.entries(counts).sort((a,b)=>b[1]-a[1]).slice(0,12);
  const x = items.map(i=>i[0]), y = items.map(i=>i[1]);
  const data = [{x,y,type:'bar'}];
  Plotly.newPlot("chart-destinos", data, {title:"Destinos mais frequentes", margin:{t:40}});
}

// draw horas line by year
function drawHoras(dfVoos){
  const byAno = {};
  dfVoos.forEach(r=>{
    const ano = r.Data ? (r.Data.slice(-4)) : (r.Ano || "");
    byAno[ano] = (byAno[ano] || 0) + (parseFloat(r.Horas_Voadas) || 0);
  });
  const anos = Object.keys(byAno).sort();
  const y = anos.map(a => byAno[a]);
  Plotly.newPlot("chart-horas", [{x:anos,y,type:'scatter',mode:'lines+markers'}], {title:"Horas voadas por ano", margin:{t:40}});
}

// render table (simple)
function renderTable(rows){
  const container = document.getElementById("table-container");
  if(rows.length===0){ container.innerHTML = "<i>Nenhum registro</i>"; return; }
  // create header
  const cols = Object.keys(rows[0]);
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const trh = document.createElement("tr");
  cols.forEach(c=>{ const th=document.createElement("th"); th.innerText=c; trh.appendChild(th); });
  thead.appendChild(trh);
  table.appendChild(thead);
  const tbody = document.createElement("tbody");
  rows.forEach(r=>{
    const tr=document.createElement("tr");
    cols.forEach(c=>{
      const td=document.createElement("td");
      td.innerText = r[c] || "";
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  container.innerHTML = "";
  container.appendChild(table);
}

// apply filters
function applyFilters(){
  const ano = document.getElementById("filter-ano").value;
  const origem = document.getElementById("filter-origem").value;
  const destino = document.getElementById("filter-destino").value;
  const orgao = document.getElementById("filter-orgao").value;
  const situacao = document.getElementById("filter-situacao").value;

  let filtered = rawRows.slice();

  if(ano !== "all") filtered = filtered.filter(r => (r.Data && r.Data.slice(-4) === ano) || (r.Ano && r.Ano === ano));
  if(origem !== "all") filtered = filtered.filter(r => r.Origem === origem);
  if(destino !== "all") filtered = filtered.filter(r => r.Destino === destino);
  if(orgao !== "all") filtered = filtered.filter(r => r.Orgao === orgao);
  if(situacao !== "all") filtered = filtered.filter(r => (r.Situacao||"").toUpperCase().includes(situacao));

  const voos = computeVoos(filtered);
  renderSummary(filtered, voos);
  drawDestinos(voos);
  drawHoras(voos);
  renderTable(filtered);
}

// download CSV (from current rawRows view)
function downloadCSV(filename, rows){
  const cols = Object.keys(rows[0]||{});
  const csv = [cols.join(",")].concat(rows.map(r => cols.map(c => `"${String(r[c]||"").replace(/"/g,'""')}"`).join(","))).join("\n");
  const blob = new Blob([csv], {type:"text/csv;charset=utf-8;"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
}

// main load
async function main(){
  try {
    const files = await fetchFilesList(); // array of paths like "data/normalized/voos_2021.csv"
    let allrows = [];
    for(const f of files){
      const rows = await fetchCSV(f);
      rows.forEach(r => {
        const norm = normalizeRow(r);
        allrows.push(norm);
      });
    }
    rawRows = allrows;
    df_voos = computeVoos(rawRows);

    // initial render
    renderSummary(rawRows, df_voos);
    buildFilters(rawRows, df_voos);
    drawDestinos(df_voos);
    drawHoras(df_voos);
    renderTable(rawRows);

    // wire events
    document.getElementById("btn-apply").onclick = applyFilters;
    document.getElementById("btn-clear").onclick = () => { document.querySelectorAll("select").forEach(s=> s.value = "all"); applyFilters(); };
    document.getElementById("btn-export-csv").onclick = ()=> downloadCSV("voos_filtrados.csv", rawRows);
    document.getElementById("btn-download-base").onclick = ()=> downloadCSV("voos_base.csv", rawRows);
    // link to raw (open first CSV)
    document.getElementById("link-open-raw").href = files[0] || "#";
  } catch(err){
    console.error(err);
    document.querySelector("main").innerHTML = `<div style="padding:18px;color:#900">Erro ao carregar dados: ${err.message}</div>`;
  }
}
main();
