const fs = require('fs');
const path = require('path');
const { createClient } = require('../frontend/node_modules/@supabase/supabase-js');

// Parse backend/.env for SERVICE_ROLE_KEY
const envPath = path.join(__dirname, '../backend/.env');
const envContent = fs.readFileSync(envPath, 'utf8');
const env = {};
envContent.split('\n').forEach(line => {
  line = line.trim();
  if (!line || line.startsWith('#')) return;
  const parts = line.split('=');
  const key = parts[0].trim();
  const val = parts.slice(1).join('=').trim();
  env[key] = val;
});

const supabaseUrl = env.NEXT_PUBLIC_SUPABASE_URL || env.SUPABASE_URL;
const supabaseKey = env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error("Missing Supabase credentials in backend/.env");
  process.exit(1);
}

// Initialize with SERVICE ROLE KEY to bypass RLS and use Admin Auth API
const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: { autoRefreshToken: false, persistSession: false }
});

const demoUsers = [
  { email: "admin@sitesync.local", password: "password123", name: "Alice Admin", role: "admin" },
  { email: "pm@sitesync.local", password: "password123", name: "Pete PM", role: "pm" },
  { email: "contractor@sitesync.local", password: "password123", name: "Craig Contractor", role: "contractor" },
  { email: "finance@sitesync.local", password: "password123", name: "Fiona Finance", role: "finance" },
];

async function seed() {
  console.log("Seeding demo data...");

  try {
    // 1. Create a demo company
    let companyId;
    const { data: companies, error: checkError } = await supabase.from('companies').select('id').eq('name', 'Demo Construction Co.');
    
    if (checkError) throw checkError;

    if (companies && companies.length > 0) {
      companyId = companies[0].id;
      console.log(`Company already exists with ID: ${companyId}`);
    } else {
      const { data: newCompany, error: insertError } = await supabase.from('companies').insert({ name: 'Demo Construction Co.' }).select();
      if (insertError) throw insertError;
      companyId = newCompany[0].id;
      console.log(`Created company with ID: ${companyId}`);
    }

    // 2. Create users
    for (const u of demoUsers) {
      console.log(`\nProcessing ${u.email}...`);
      
      // Check if user exists in our table
      const { data: existingUsers } = await supabase.from('users').select('id').eq('email', u.email);
      if (existingUsers && existingUsers.length > 0) {
        console.log(`User ${u.email} already exists in DB.`);
        continue;
      }

      // Create in Supabase Auth
      console.log(`Creating ${u.email} in Supabase Auth...`);
      const { data: authData, error: authError } = await supabase.auth.admin.createUser({
        email: u.email,
        password: u.password,
        email_confirm: true
      });

      if (authError) {
        console.error(`Auth Error: ${authError.message}`);
        // If it says already registered, we can proceed to insert into DB anyway, but let's be careful
        if (!authError.message.includes('already been registered')) {
            continue;
        }
      }

      // Insert into our DB
      const { error: dbError } = await supabase.from('users').insert({
        company_id: companyId,
        name: u.name,
        email: u.email,
        password_hash: "supa-auth", // placeholder
        role: u.role,
        is_active: true
      });

      if (dbError) {
        console.error(`DB Error: ${dbError.message}`);
      } else {
        console.log(`✅ Successfully seeded ${u.email} (role: ${u.role})`);
      }
    }
    
    console.log("\nSeeding complete!");

  } catch (error) {
    console.error("Seed failed:", error);
  }
}

seed();
