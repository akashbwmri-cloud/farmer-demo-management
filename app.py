import streamlit as st
import pandas as pd
from datetime import date, datetime
from pathlib import Path

st.set_page_config(page_title="Farmer Demo System - Step 5", page_icon="🌽", layout="wide")

USE_SUPABASE = False
supabase = None
try:
    from supabase import create_client
    if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
        supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
        USE_SUPABASE = True
except Exception:
    pass

def select_df(table):
    if not USE_SUPABASE:
        return pd.DataFrame()
    r = supabase.table(table).select("*").order("id", desc=True).execute()
    return pd.DataFrame(r.data or [])

def next_code():
    df = select_df("demos")
    if df.empty: return "DEMO-0001"
    n = pd.to_numeric(df["demo_code"].astype(str).str.extract(r"(\d+)$")[0], errors="coerce").dropna()
    return f"DEMO-{int(n.max())+1:04d}" if len(n) else "DEMO-0001"

def upload_photo(f, code, prefix):
    if not f or not USE_SUPABASE: return None
    name = f"{code}_{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{Path(f.name).suffix.lower()}"
    supabase.storage.from_("field-photos").upload(name, f.getvalue(),
        {"content-type": f.type, "upsert": "true"})
    return supabase.storage.from_("field-photos").get_public_url(name)

def insert(table, data):
    supabase.table(table).insert(data).execute()

if not USE_SUPABASE:
    st.warning("Online database is not connected yet. Follow README to connect Supabase.")

st.title("🌽 Farmer Demonstration Management System")
st.caption("Step 5 — Online Farmer Entry + One-click GPS + Photo + Admin Dashboard")
page = st.sidebar.radio("Open", ["👨‍🌾 Farmer Entry","🏠 Admin Dashboard","🗺️ Demo Map","📊 All Data","📥 Export"])

def get_gps():
    try:
        from streamlit_geolocation import streamlit_geolocation
        loc = streamlit_geolocation()
        if loc and loc.get("latitude") is not None:
            return float(loc["latitude"]), float(loc["longitude"]), float(loc.get("accuracy") or 0)
    except Exception:
        pass
    return 0.0, 0.0, 0.0

if page == "👨‍🌾 Farmer Entry":
    st.header("👨‍🌾 Farmer Mobile Data Entry")
    mode = st.radio("Entry type", ["Register New Demo","Update Existing Demo"], horizontal=True)

    if mode == "Register New Demo":
        with st.form("new"):
            a,b=st.columns(2)
            with a:
                name=st.text_input("Farmer Name *"); mobile=st.text_input("Mobile Number")
                district=st.text_input("District *"); upazila=st.text_input("Upazila *")
                union=st.text_input("Union"); village=st.text_input("Village")
            with b:
                crop=st.text_input("Crop","Maize"); variety=st.text_input("Variety")
                sow=st.date_input("Sowing Date",date.today())
                area=st.number_input("Demo Area (decimal)",min_value=0.1,value=20.0)
            st.markdown("### 📍 GPS")
            lat,lon,acc=get_gps()
            if lat and lon: st.success(f"GPS captured: {lat:.6f}, {lon:.6f} | Accuracy: {acc:.1f} m")
            else: st.info("Tap the location button and allow location permission.")
            photo=st.file_uploader("📸 Take/Upload Field Photo",type=["jpg","jpeg","png"])
            submitted=st.form_submit_button("Submit Farmer/Demo")
        if submitted:
            if not name or not district or not upazila:
                st.error("Farmer Name, District and Upazila are required.")
            elif not USE_SUPABASE:
                st.error("First connect Supabase.")
            else:
                code=next_code()
                photo_url=upload_photo(photo,code,"demo") if photo else None
                insert("demos",{"demo_code":code,"farmer_name":name,"mobile":mobile,
                    "district":district,"upazila":upazila,"union_name":union,"village":village,
                    "crop":crop,"variety":variety,"sowing_date":str(sow),"area_decimal":area,
                    "latitude":lat or None,"longitude":lon or None,"gps_accuracy":acc or None,
                    "photo_path":photo_url,"created_at":datetime.now().isoformat(timespec="seconds")})
                st.success(f"Submitted successfully. Demo ID: {code}")
                st.rerun()
    else:
        df=select_df("demos")
        if df.empty: st.warning("No demo registered yet.")
        else:
            code=st.selectbox("Select Demo ID",df.demo_code.tolist())
            row=df[df.demo_code==code].iloc[0]
            st.write(f"**Farmer:** {row.farmer_name} | **Village:** {row.village} | **Variety:** {row.variety}")
            with st.form("update"):
                ed=st.date_input("Entry Date",date.today())
                fertilizer=st.text_area("🧪 Fertilizer applied / dose")
                irrigation=st.text_area("💧 Irrigation date / details")
                condition=st.selectbox("🌱 Crop Condition",["Excellent","Good","Average","Poor"])
                pest=st.text_area("🐛 Pest/Disease"); feedback=st.text_area("📝 Farmer Feedback")
                st.markdown("### 📍 Current Field GPS")
                lat,lon,acc=get_gps()
                if not lat: lat=float(row.latitude or 0); lon=float(row.longitude or 0); acc=float(row.gps_accuracy or 0)
                photo=st.file_uploader("📸 Field Photo",type=["jpg","jpeg","png"])
                submitted=st.form_submit_button("Submit Field Update")
            if submitted and USE_SUPABASE:
                photo_url=upload_photo(photo,code,"field") if photo else None
                insert("field_data",{"demo_code":code,"entry_date":str(ed),"fertilizer":fertilizer,
                    "irrigation":irrigation,"crop_condition":condition,"pest_disease":pest,
                    "farmer_feedback":feedback,"latitude":lat or None,"longitude":lon or None,
                    "gps_accuracy":acc or None,"photo_path":photo_url,
                    "created_at":datetime.now().isoformat(timespec="seconds")})
                st.success("Field update submitted."); st.rerun()

elif page == "🏠 Admin Dashboard":
    st.header("🏠 Admin Dashboard"); df=select_df("demos"); fd=select_df("field_data")
    if df.empty: st.info("No demos yet.")
    else:
        a,b,c,d=st.columns(4)
        a.metric("Total Demo",len(df)); b.metric("Farmers",df["mobile"].replace("",pd.NA).nunique())
        c.metric("GPS Demo",int(df["latitude"].notna().sum())); d.metric("Field Updates",len(fd))
        x,y=st.columns(2)
        with x: st.dataframe(df.groupby("district").size().reset_index(name="Demo"),use_container_width=True,hide_index=True)
        with y: st.dataframe(df.groupby(["district","upazila"]).size().reset_index(name="Demo"),use_container_width=True,hide_index=True)
        cols=["demo_code","farmer_name","mobile","district","upazila","union_name","village","variety","latitude","longitude"]
        st.dataframe(df[cols],use_container_width=True,hide_index=True)

elif page == "🗺️ Demo Map":
    st.header("🗺️ Demo GPS Map"); df=select_df("demos")
    if df.empty: st.warning("No GPS data yet.")
    else:
        m=df.dropna(subset=["latitude","longitude"])
        if m.empty: st.warning("No GPS data yet.")
        else:
            st.map(m.rename(columns={"latitude":"lat","longitude":"lon"})[["lat","lon"]])
            st.dataframe(m[["demo_code","farmer_name","district","upazila","latitude","longitude","gps_accuracy"]],use_container_width=True,hide_index=True)

elif page == "📊 All Data":
    st.header("📊 All Farmer Field Data")
    st.subheader("Field Updates"); st.dataframe(select_df("field_data"),use_container_width=True,hide_index=True)
    st.subheader("Harvest"); st.dataframe(select_df("harvest"),use_container_width=True,hide_index=True)

else:
    st.header("📥 Export")
    for table,fn,title in [("demos","demos.csv","Demo/Farmer"),("field_data","field_updates.csv","Field Updates"),("harvest","harvest.csv","Harvest")]:
        df=select_df(table)
        st.download_button(f"Download {title} CSV",df.to_csv(index=False).encode("utf-8-sig"),fn,"text/csv")
