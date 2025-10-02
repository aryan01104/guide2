#!/bin/bash

echo "Redeploying the 'setting_score' edge function..."
supabase functions deploy setting_score --no-verify-jwt
echo "Redeployment complete."
