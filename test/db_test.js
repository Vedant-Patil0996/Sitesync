const fs = require('fs');
const path = require('path');

// Manually parse frontend/.env to avoid needing dotenv package
const envPath = path.join(__dirname, '../frontend/.env');
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

const supabaseUrl = env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error("Missing Supabase credentials in frontend/.env");
  process.exit(1);
}

// We will use the supabase-js client already installed in the frontend
const { createClient } = require('../frontend/node_modules/@supabase/supabase-js');

const supabase = createClient(supabaseUrl, supabaseKey);

async function testConnection() {
  console.log(`Attempting to connect to Supabase at: ${supabaseUrl}`);
  
  // Test by querying the companies table we created in the schema
  const { data, error } = await supabase.from('companies').select('*').limit(3);
  
  if (error) {
    console.error("\n❌ FAILED to query Supabase.");
    console.error(error.message);
    if (error.message.includes('relation "public.companies" does not exist')) {
        console.error("The tables don't exist yet. Make sure to run schema.sql in Supabase SQL editor!");
    }
  } else {
    console.log("\n✅ Successfully connected to Supabase!");
    console.log(`Found ${data.length} records in 'companies' table.`);
    if (data.length > 0) {
      console.log(data);
    } else {
      console.log("(Table is empty, which is normal for a fresh database)");
    }
  }
}

testConnection();
