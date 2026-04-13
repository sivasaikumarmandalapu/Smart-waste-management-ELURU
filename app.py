from flask import Flask, render_template, jsonify
import random
import requests

app = Flask(__name__)

# --- Generate bins near Koppuravuru ---
bins = []
for i in range(1, 51):
    bins.append({
        "id": f"Bin{i}",
       "lat": 16.7107 + random.uniform(-0.01, 0.01),
       "lng": 81.0952 + random.uniform(-0.01, 0.01),
        "type": random.choice(["Plastic","Organic","Metal","Glass"]),
        "status": "alive",
        "fill": random.randint(10,60)
    })

# --- 10 Trucks near Koppuravuru ---
collectors = []
for i in range(1,11):
    collectors.append({
        "id": f"Truck{i}",
        "driver": f"Driver{i}",
        "lat": 16.7107 + random.uniform(-0.005, 0.005),
        "lng": 81.0952 + random.uniform(-0.005, 0.005),
        "status":"alive",
        "collected":0,
        "target": None,
        "route": [],
        "route_index":0
    })

# --- Dumpyard location ---
dumpyard = {"lat":16.700797, "lng":81.058968}

log = []

# --- Routing ---
def get_route(start,end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&geometries=geojson"
    try:
        r = requests.get(url, timeout=5).json()
        coords = r['routes'][0]['geometry']['coordinates']
        return [(lat,lng) for lng,lat in coords]
    except:
        return [start,end]

# --- Truck movement ---
def move_trucks():
    for truck in collectors:
        if truck["route"] and truck["route_index"] < len(truck["route"]):
            truck["lat"], truck["lng"] = truck["route"][truck["route_index"]]
            truck["route_index"] += 1
            if truck["route_index"] >= len(truck["route"]):
                if truck["target"] and truck["target"]!="DUMPYARD":
                    log.append({"time":"Now","truck":truck["id"],"bin":truck["target"]})
                    truck["collected"] += 1
                    for b in bins:
                        if b["id"]==truck["target"]:
                            b["fill"]=0
                            break
                    truck["route"] = get_route((truck["lat"],truck["lng"]),(dumpyard["lat"],dumpyard["lng"]))
                    truck["route_index"]=0
                    truck["target"]="DUMPYARD"
                else:
                    truck["target"]=None
                    truck["route"]= []
        else:
            if not truck["target"]:
                full_bins = [b for b in bins if b["fill"]>=80 and b["status"]=="alive"]
                if full_bins:
                    target_bin=random.choice(full_bins)
                    truck["target"]=target_bin["id"]
                    truck["route"]=get_route((truck["lat"],truck["lng"]),(target_bin["lat"],target_bin["lng"]))
                    truck["route_index"]=0

# --- Routes ---
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/bins")
def get_bins():
    for b in bins:
        if b["status"]=="alive":
            b["fill"]=min(100,b["fill"]+random.randint(0,5))
            if random.random()<0.01:
                b["status"]="failed"
    return jsonify(bins)

@app.route("/collectors")
def get_collectors():
    move_trucks()
    return jsonify({"collectors":collectors,"dumpyard":dumpyard,"bins":bins})

@app.route("/log")
def get_log():
    return jsonify(log)

if __name__=="__main__":
    app.run(debug=True)
