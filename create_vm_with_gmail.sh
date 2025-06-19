cat > create_vm_fixed.sh << EOF
#!/bin/bash

# Configuración
PROJECT_ID="lab-asistente-turistico"
ZONE="us-central1-a"
VM_NAME="vm-chatbots-campeche"
EMAIL="asandoval@redmagisterial.com"

# 1. Asignar los roles necesarios a tu cuenta
gcloud projects add-iam-policy-binding "lab-asistente-turistico" \
    --member="user:asandoval@redmagisterial.com" \
    --role="roles/compute.osLogin" || true

gcloud projects add-iam-policy-binding "lab-asistente-turistico" \
    --member="user:asandoval@redmagisterial.com" \
    --role="roles/compute.instanceAdmin.v1" || true

# 2. Crear la instancia especificando tu cuenta como usuario OS Login
gcloud compute instances create "vm-chatbots-campeche" \
    --zone="us-central1-a" \
    --image-family="debian-11" \
    --image-project="debian-cloud" \
    --metadata="google-compute-default-owner=asandoval@redmagisterial.com" \
    --scopes="cloud-platform"
EOF

chmod +x create_vm_fixed.sh
./create_vm_fixed.sh