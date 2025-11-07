// node/router/index.js
const express = require('express');
const bodyParser = require('body-parser');

const app = express();
app.use(express.json());

const MODEL_URL = process.env.MODEL_URL || 'http://model_server:8000/predict';
const PSP_ENDPOINTS = {
  'Axis_PSP': process.env.PSP_AXIS || 'http://psp_axis:9000/process',
  'HDFC_PSP': process.env.PSP_HDFC || 'http://psp_hdfc:9001/process',
  'SBI_PSP': process.env.PSP_SBI || 'http://psp_sbi:9002/process'
};

function chooseBackup(primary){
  const prefs = ['HDFC_PSP','SBI_PSP','Axis_PSP'];
  for(const p of prefs){ if(p !== primary) return p; }
  return primary;
}

app.post('/route', async (req,res) => {
  const txn = req.body || {};
  txn.txn_id = txn.txn_id || ('txn-' + Date.now());

  // call Python model server using global fetch (Node 18+)
  let score = 0.5;
  try {
    const r = await fetch(MODEL_URL, {
      method: 'POST',
      body: JSON.stringify(txn),
      headers: {'Content-Type':'application/json'},
      // fetch in Node accepts timeout with AbortController if needed; keep simple
    });
    const jr = await r.json();
    score = Number(jr.failure_probability || 0.0);
  } catch(err) {
    console.error('Model server error', err.message || err);
    score = 0.5;
  }

  let initial = txn.psp_candidate || 'Axis_PSP';
  let chosen = initial;
  if(score > 0.6) chosen = chooseBackup(initial);

  // call chosen PSP
  let pspResp = { error: 'psp_unreachable' };
  try{
    const pr = await fetch(PSP_ENDPOINTS[chosen], {
      method: 'POST',
      body: JSON.stringify(txn),
      headers: {'Content-Type':'application/json'}
    });
    pspResp = await pr.json();
  }catch(err){
    console.error('PSP call error', err.message || err);
    pspResp = { error: err.message || String(err) };
  }

  res.json({
    txn_id: txn.txn_id,
    predicted_fail_prob: score,
    initial_psp: initial,
    routed_to: chosen,
    psp_response: pspResp
  });
});

app.get('/health', (req,res)=>res.json({status:'ok'}));
const PORT = process.env.PORT || 8080;
app.listen(PORT, ()=>console.log('Router listening on', PORT));
