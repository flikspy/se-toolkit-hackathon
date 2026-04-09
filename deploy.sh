#!/bin/bash

# Deployment script for Shared Grocery List
# Target VM: 10.93.24.144 (Ubuntu 24.04, 2 cores, 4GB RAM)

VM_IP="10.93.24.144"
VM_USER="root"
VM_PASSWORD="Eeeddd11"
PROJECT_NAME="sharedgrocery"
REMOTE_PATH="/root/$PROJECT_NAME"

echo "🚀 Starting deployment to $VM_IP..."

# Step 1: Check if project is in git repo
echo ""
echo "📦 Step 1: Checking git repository..."
if git status >/dev/null 2>&1; then
    echo "✅ Git repository found"
    
    # Commit any uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        echo "⚠️  Found uncommitted changes, committing..."
        git add .
        git commit -m "Deploy to university VM $(date '+%Y-%m-%d %H:%M:%S')"
    fi
    
    REMOTE_CLONE=true
else
    echo "⚠️  Not a git repository, will use scp instead"
    REMOTE_CLONE=false
fi

# Step 2: Install Docker on VM
echo ""
echo "🐳 Step 2: Installing Docker on VM..."
sshpass -p "$VM_PASSWORD" ssh -o StrictHostKeyChecking=no $VM_USER@$VM_IP << 'EOF'
# Check if Docker is already installed
if command -v docker &> /dev/null; then
    echo "✅ Docker already installed: $(docker --version)"
else
    echo "Installing Docker..."
    apt-get update
    apt-get install -y ca-certificates curl gnupg lsb-release
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Enable and start Docker
    systemctl enable docker
    systemctl start docker
    
    echo "✅ Docker installed: $(docker --version)"
fi

# Verify Docker Compose
if docker compose version &> /dev/null; then
    echo "✅ Docker Compose available: $(docker compose version)"
else
    echo "❌ Docker Compose not found!"
    exit 1
fi
EOF

# Step 3: Transfer project to VM
echo ""
echo "📤 Step 3: Transferring project to VM..."

if [ "$REMOTE_CLONE" = true ]; then
    # Get git remote URL
    GIT_REMOTE=$(git remote get-url origin 2>/dev/null)
    if [ -n "$GIT_REMOTE" ]; then
        echo "Using git clone from: $GIT_REMOTE"
        sshpass -p "$VM_PASSWORD" ssh -o StrictHostKeyChecking=no $VM_USER@$VM_IP << EOF
# Stop existing containers if running
cd $REMOTE_PATH 2>/dev/null && docker compose down 2>/dev/null || true
rm -rf $REMOTE_PATH
git clone $GIT_REMOTE $REMOTE_PATH
cd $REMOTE_PATH
echo "✅ Project cloned successfully"
EOF
    else
        echo "⚠️  No git remote found, falling back to scp..."
        REMOTE_CLONE=false
    fi
fi

if [ "$REMOTE_CLONE" = false ]; then
    echo "Using scp to transfer project..."
    # Create remote directory
    sshpass -p "$VM_PASSWORD" ssh -o StrictHostKeyChecking=no $VM_USER@$VM_IP "mkdir -p $REMOTE_PATH"
    
    # Stop existing containers if running
    sshpass -p "$VM_PASSWORD" ssh -o StrictHostKeyChecking=no $VM_USER@$VM_IP "cd $REMOTE_PATH 2>/dev/null && docker compose down 2>/dev/null || true"
    
    # Transfer project (exclude unnecessary files)
    rsync -avz --progress \
        --exclude '.git' \
        --exclude '.pytest_cache' \
        --exclude '__pycache__' \
        --exclude 'node_modules' \
        --exclude '.venv' \
        --exclude '.env' \
        --exclude '*.pyc' \
        -e "sshpass -p $VM_PASSWORD ssh -o StrictHostKeyChecking=no" \
        ./ $VM_USER@$VM_IP:$REMOTE_PATH/
    
    echo "✅ Project transferred successfully"
fi

# Step 4: Build and start containers
echo ""
echo "🏗️  Step 4: Building and starting containers..."
sshpass -p "$VM_PASSWORD" ssh -o StrictHostKeyChecking=no $VM_USER@$VM_IP << EOF
cd $REMOTE_PATH

echo "Stopping existing containers..."
docker compose down

echo "Building and starting containers..."
docker compose up -d --build

echo "✅ Containers started"
EOF

# Step 5: Wait for services to be ready
echo ""
echo "⏳ Step 5: Waiting for services to be ready..."
sleep 15

# Step 6: Check service health
echo ""
echo "🔍 Step 6: Checking service health..."
sshpass -p "$VM_PASSWORD" ssh -o StrictHostKeyChecking=no $VM_USER@$VM_IP << EOF
cd $REMOTE_PATH

echo "Container status:"
docker compose ps

echo ""
echo "Checking backend health..."
for i in {1..10}; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    fi
    echo "Waiting for backend... (attempt $i/10)"
    sleep 3
done

echo ""
echo "Checking frontend..."
if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is accessible!"
else
    echo "⚠️  Frontend might still be starting..."
fi
EOF

# Step 7: Final status
echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Access your application at:"
echo "  Frontend: http://$VM_IP:3000"
echo "  Backend API: http://$VM_IP:3000/api/docs (proxied)"
echo ""
echo "To check logs:"
echo "  ssh root@$VM_IP (password: $VM_PASSWORD)"
echo "  cd $REMOTE_PATH && docker compose logs -f"
echo ""
echo "To stop:"
echo "  cd $REMOTE_PATH && docker compose down"
