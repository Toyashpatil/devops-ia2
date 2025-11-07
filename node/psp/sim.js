// node/psp/sim.js
const express = require('express');
const bodyParser = require('body-parser');
const app = express();
app.use(bodyParser.json());

const BASE_FAIL = parseFloat(process.env.BASE_FAIL || '0.03');

function rand(){ return Math.random(); }

app.post('/process', (req, res) => {
  const txn = req.body || {};
  const prob = BASE_FAIL + 0.0001*(Number(txn.amount||0)) + 0.001*((Number(txn.network_latency_ms)||100)/100);
  const success = rand() > prob;
  res.json({
    txn_id: txn.txn_id || null,
    status: success ? 'success' : 'failure',
    psp_fail_prob: Number(prob.toFixed(4))
  });
});

app.get('/health', (req,res)=>res.json({status:'ok', base_fail: BASE_FAIL}));
const PORT = process.env.PORT || 9000;
app.listen(PORT, ()=>console.log('PSP sim listening on', PORT, 'base_fail=', BASE_FAIL));
