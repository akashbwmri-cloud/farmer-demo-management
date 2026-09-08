import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
from pathlib import Path

APP = Path(__file__).parent
DB = APP / "demo_app.db"
PHOTO_DIR = APP / "photos"
PHOTO_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Farmer Demo System - Step 4", page_icon="🌽", layout="wide")

def getdb():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init():
    c = getdb()
    c.execute("""CREATE TABLE IF NOT EXISTS demos(
      id INTEGER PRIMARY KEY AUTOINCREMENT, demo_code TEXT UNIQUE,
      farmer_name TEXT, mobile TEXT, district TEXT, upazila TEXT,
      union_name TEXT, village TEXT, crop TEXT, variety TEXT,
      sowing_date TEXT, area_decimal REAL, latitude REAL, longitude REAL,
      gps_accuracy REAL, photo_path TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS field_data(
      id INTEGER PRIMARY KEY AUTOINCREMENT, demo_code TEXT, entry_date TEXT,
      fertilizer TEXT, irrigation TEXT, crop_condition TEXT,
      pest_disease TEXT, farmer_feedback TEXT, latitude REAL,
      longitude REAL, gps_accuracy REAL, photo_path TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS harvest(
      id INTEGER PRIMARY KEY AUTOINCREMENT, demo_code TEXT, harvest_date TEXT,
      grain_kg REAL, area_decimal REAL, yield_t_ha REAL, remarks TEXT)""")
    c.commit(); c.close()

def demo_df():
    c=getdb(); df=pd.read_sql_query("SELECT * FROM demos ORDER BY id DESC",c); c.close(); return df

def next_code():
    c=getdb(); n=c.execute("SELECT COUNT(*) FROM demos").fetchone()[0]+1
    code=f"DEMO-{n:04d}"
    while c.execute("SELECT 1 FROM demos WHERE demo_code=?",(code,)).fetchone():
        n+=1; code=f"DEMO-{n:04d}"
    c.close(); return code

init()

st.title("🌽 Farmer Demonstration Management System")
st.caption("Step 4 — Farmer Mobile Data Entry + GPS + Photo + Admin Dashboard")

page=st.sidebar.radio("Open",["👨‍🌾 Farmer Entry","🏠 Admin Dashboard","🗺️ Demo Map","📊 All Data","📥 Export"])

GPS_HTML = """
<button onclick="getLocation()" style="padding:12px 20px;font-size:16px">📍 Get My Location</button>
<p id="status">GPS not captured.</p>
<script>
function getLocation(){
 const s=document.getElementById('status');
 if(!navigator.geolocation){s.innerText='GPS is not supported by this browser.';return;}
 s.innerText='Requesting location permission...';
 navigator.geolocation.getCurrentPosition(function(p){
   s.innerText='GPS captured: '+p.coords.latitude.toFixed(6)+', '+p.coords.longitude.toFixed(6)+' (accuracy '+Math.round(p.coords.accuracy)+' m).';
 },function(e){s.innerText='GPS error: '+e.message;},
 {enableHighAccuracy:true,timeout:15000,maximumAge:0});
}
</script>
"""

if page=="👨‍🌾 Farmer Entry":
    st.header("👨‍🌾 Farmer Mobile Data Entry")
    st.info("Farmer can use this page from a phone. Allow Location permission when asked.")
    df=demo_df()
    mode=st.radio("Entry type",["Register New Demo","Update Existing Demo"],horizontal=True)

    if mode=="Register New Demo":
        with st.form("new"):
            a,b=st.columns(2)
            with a:
                name=st.text_input("Farmer Name *")
                mobile=st.text_input("Mobile Number")
                district=st.text_input("District *")
                upazila=st.text_input("Upazila *")
                union=st.text_input("Union")
                village=st.text_input("Village")
            with b:
                crop=st.text_input("Crop","Maize")
                variety=st.text_input("Variety")
                sow=date.today()
                sow=st.date_input("Sowing Date",sow)
                area=st.number_input("Demo Area (decimal)",min_value=0.1,value=20.0)
            st.markdown("### 📍 GPS")
            st.components.v1.html(GPS_HTML,height=120)
            lat=st.number_input("Latitude (paste captured value)",value=0.0,format="%.6f")
            lon=st.number_input("Longitude (paste captured value)",value=0.0,format="%.6f")
            acc=st.number_input("GPS Accuracy (m)",min_value=0.0,value=0.0)
            photo=st.file_uploader("📸 Take/Upload Field Photo",type=["jpg","jpeg","png"])
            if st.form_submit_button("Submit Farmer/Demo"):
                if not name or not district or not upazila:
                    st.error("Farmer Name, District and Upazila are required.")
                else:
                    code=next_code(); pp=""
                    if photo:
                        p=PHOTO_DIR/(code+"_"+Path(photo.name).name)
                        p.write_bytes(photo.getbuffer()); pp=str(p)
                    c=getdb()
                    c.execute("""INSERT INTO demos(demo_code,farmer_name,mobile,district,upazila,
                    union_name,village,crop,variety,sowing_date,area_decimal,latitude,longitude,
                    gps_accuracy,photo_path,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (code,name,mobile,district,upazila,union,village,crop,variety,str(sow),area,
                     lat or None,lon or None,acc or None,pp,datetime.now().isoformat(timespec="seconds")))
                    c.commit(); c.close()
                    st.success("Submitted successfully. Demo ID: "+code)
                    st.rerun()
    else:
        if df.empty:
            st.warning("No demo registered yet.")
        else:
            code=st.selectbox("Select Demo ID",df.demo_code.tolist())
            row=df[df.demo_code==code].iloc[0]
            st.write(f"**Farmer:** {row.farmer_name} | **Village:** {row.village} | **Variety:** {row.variety}")
            with st.form("update"):
                ed=st.date_input("Entry Date",date.today())
                fertilizer=st.text_area("🧪 Fertilizer applied / dose")
                irrigation=st.text_area("💧 Irrigation date / details")
                condition=st.selectbox("🌱 Crop Condition",["Excellent","Good","Average","Poor"])
                pest=st.text_area("🐛 Pest/Disease")
                feedback=st.text_area("📝 Farmer Feedback")
                st.markdown("### 📍 Current Field GPS")
                st.components.v1.html(GPS_HTML,height=120)
                lat=st.number_input("Latitude",value=float(row.latitude or 0),format="%.6f")
                lon=st.number_input("Longitude",value=float(row.longitude or 0),format="%.6f")
                acc=st.number_input("Accuracy (m)",min_value=0.0,value=float(row.gps_accuracy or 0))
                photo=st.file_uploader("📸 Field Photo",type=["jpg","jpeg","png"])
                if st.form_submit_button("Submit Field Update"):
                    pp=""
                    if photo:
                        p=PHOTO_DIR/(code+"_field_"+datetime.now().strftime("%Y%m%d_%H%M%S")+Path(photo.name).suffix.lower())
                        p.write_bytes(photo.getbuffer()); pp=str(p)
                    c=getdb()
                    c.execute("""INSERT INTO field_data(demo_code,entry_date,fertilizer,irrigation,
                    crop_condition,pest_disease,farmer_feedback,latitude,longitude,gps_accuracy,
                    photo_path,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (code,str(ed),fertilizer,irrigation,condition,pest,feedback,lat or None,
                     lon or None,acc or None,pp,datetime.now().isoformat(timespec="seconds")))
                    c.commit(); c.close()
                    st.success("Field update submitted.")

elif page=="🏠 Admin Dashboard":
    st.header("🏠 Admin Dashboard")
    df=demo_df()
    c=getdb()
    fd=pd.read_sql_query("SELECT * FROM field_data",c)
    hv=pd.read_sql_query("SELECT * FROM harvest",c)
    c.close()
    if df.empty:
        st.info("No demos yet.")
    else:
        a,b,c,d=st.columns(4)
        a.metric("Total Demo",len(df))
        b.metric("Farmers",df.mobile.replace("",pd.NA).nunique())
        c.metric("GPS Demo",int(df.latitude.notna().sum()))
        d.metric("Field Updates",len(fd))
        st.divider()
        x,y=st.columns(2)
        with x:
            st.markdown("### District-wise")
            st.dataframe(df.groupby("district").size().reset_index(name="Demo"),use_container_width=True,hide_index=True)
        with y:
            st.markdown("### Upazila-wise")
            st.dataframe(df.groupby(["district","upazila"]).size().reset_index(name="Demo"),use_container_width=True,hide_index=True)
        st.markdown("### Recent Farmer/Demo")
        st.dataframe(df[["demo_code","farmer_name","mobile","district","upazila","union_name","village","variety","latitude","longitude"]],use_container_width=True,hide_index=True)

elif page=="🗺️ Demo Map":
    st.header("🗺️ Demo GPS Map")
    df=demo_df()
    m=df.dropna(subset=["latitude","longitude"])
    if m.empty: st.warning("No GPS data yet.")
    else:
        st.map(m.rename(columns={"latitude":"lat","longitude":"lon"})[["lat","lon"]])
        st.dataframe(m[["demo_code","farmer_name","district","upazila","union_name","latitude","longitude","gps_accuracy"]],use_container_width=True,hide_index=True)

elif page=="📊 All Data":
    st.header("📊 All Farmer Field Data")
    c=getdb()
    fd=pd.read_sql_query("SELECT * FROM field_data ORDER BY id DESC",c)
    hv=pd.read_sql_query("SELECT * FROM harvest ORDER BY id DESC",c)
    c.close()
    st.subheader("Field Updates")
    st.dataframe(fd,use_container_width=True,hide_index=True)
    st.subheader("Harvest")
    st.dataframe(hv,use_container_width=True,hide_index=True)

else:
    st.header("📥 Export")
    df=demo_df()
    c=getdb()
    fd=pd.read_sql_query("SELECT * FROM field_data",c)
    hv=pd.read_sql_query("SELECT * FROM harvest",c)
    c.close()
    st.download_button("Download Demo/Farmer CSV",df.to_csv(index=False).encode("utf-8-sig"),"demos.csv","text/csv")
    st.download_button("Download Field Updates CSV",fd.to_csv(index=False).encode("utf-8-sig"),"field_updates.csv","text/csv")
    st.download_button("Download Harvest CSV",hv.to_csv(index=False).encode("utf-8-sig"),"harvest.csv","text/csv")
