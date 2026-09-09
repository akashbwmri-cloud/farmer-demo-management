# Step 5 — Online Farmer Demo Management

This version is prepared for Streamlit Community Cloud + Supabase.
It adds online database support and one-click browser GPS via streamlit-geolocation.

## Setup
1. Create a project at https://supabase.com/
2. Supabase -> SQL Editor -> New query.
3. Run all SQL from `supabase_schema.sql`.
4. Supabase -> Project Settings -> API. Copy Project URL and the publishable/anon key.
5. Upload `app.py`, `requirements.txt`, `supabase_schema.sql`, and `README.md` to your GitHub repository. Do NOT upload `demo_app.db`.
6. Deploy the GitHub repository at https://share.streamlit.io/
7. In Streamlit Cloud: Settings -> Secrets, add:
SUPABASE_URL = "your-project-url"
SUPABASE_KEY = "your-publishable-or-anon-key"
8. Reboot/redeploy.

After deployment, give the Streamlit HTTPS link to farmers. They can use Farmer Entry from their phones, allow GPS permission, take a photo, and submit data.

Important: this is an MVP with anonymous database policies so submissions can work without login. Before official large-scale use, add authentication/role-based access.
