# python/generate_data.py
import csv, random, uuid
import numpy as np

PSPS = [
    {"name":"Axis_PSP","base_fail":0.045},
    {"name":"HDFC_PSP","base_fail":0.02},
    {"name":"SBI_PSP","base_fail":0.03},
]

APPS = ["GooglePay","PhonePe","Paytm"]
BANKS = ["SBI","HDFC","ICICI","Axis","YesBank"]

def rand_normal(mu=0, sigma=1):
    return np.random.normal(mu, sigma)

def sample_txn(i):
    psp = random.choice(PSPS)
    src = random.choice(BANKS)
    dest = random.choice(BANKS)
    amount = max(10, int(abs(rand_normal(1200, 800))))
    hour = random.randint(0,23)
    weekday = random.randint(0,6)
    device = random.choice(["Android","iOS"])
    network_latency = max(20, int(abs(rand_normal(150, 80))))
    recent_fail = min(0.5, abs(random.random()*0.1 + (0.05 if hour in [18,19,20] else 0)))
    psp_success = 1 - psp["base_fail"] + random.normalvariate(0,0.005)
    fail_prob = psp["base_fail"] + 0.0001*amount + 0.001*(network_latency/100) + 0.2*recent_fail
    fail_prob = min(0.95, max(0, fail_prob))
    status = "failure" if random.random() < fail_prob else "success"
    return {
        "txn_id": str(uuid.uuid4()),
        "app": random.choice(APPS),
        "psp_candidate": psp["name"],
        "src_bank": src,
        "dest_bank": dest,
        "amount": amount,
        "channel": "UPI",
        "device_type": device,
        "network_latency_ms": network_latency,
        "hour": hour,
        "weekday": weekday,
        "recent_fail_rate_src_dest_5m": round(recent_fail,3),
        "psp_success_rate_5m": round(psp_success,3),
        "status": status
    }

def main(n=20000, out="transactions.csv"):
    keys = ["txn_id","app","psp_candidate","src_bank","dest_bank","amount","channel","device_type","network_latency_ms","hour","weekday","recent_fail_rate_src_dest_5m","psp_success_rate_5m","status"]
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for i in range(n):
            w.writerow(sample_txn(i))
    print("Saved", out)

if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv)>1 else 20000
    main(n)
