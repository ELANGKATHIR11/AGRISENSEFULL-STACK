#!/bin/bash
# AgriSense Production Deployment Script
# Comprehensive deployment automation with safety checks

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-production}"
NAMESPACE="agrisense-${DEPLOYMENT_ENV}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-ghcr.io/your-org}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
KUBE_CONFIG="${KUBE_CONFIG:-$HOME/.kube/config}"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "docker is not installed or not in PATH"
    fi
    
    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        log_warning "helm is not installed - some features may not work"
    fi
    
    # Check kubectl connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
    fi
    
    log_success "Prerequisites check passed"
}

# Build and push Docker images
build_and_push_images() {
    log "Building and pushing Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build main application image
    log "Building main application image..."
    docker build -t "${DOCKER_REGISTRY}/agrisense:${IMAGE_TAG}" .
    docker push "${DOCKER_REGISTRY}/agrisense:${IMAGE_TAG}"
    
    # Build Celery worker image
    log "Building Celery worker image..."
    docker build -f Dockerfile.celery -t "${DOCKER_REGISTRY}/agrisense-celery:${IMAGE_TAG}" .
    docker push "${DOCKER_REGISTRY}/agrisense-celery:${IMAGE_TAG}"
    
    log_success "Docker images built and pushed successfully"
}

# Create namespace if it doesn't exist
create_namespace() {
    log "Ensuring namespace ${NAMESPACE} exists..."
    
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        kubectl create namespace "$NAMESPACE"
        kubectl label namespace "$NAMESPACE" env="$DEPLOYMENT_ENV"
        log_success "Namespace ${NAMESPACE} created"
    else
        log_success "Namespace ${NAMESPACE} already exists"
    fi
}

# Deploy secrets and configmaps
deploy_configuration() {
    log "Deploying configuration..."
    
    # Check if .env file exists
    ENV_FILE="${PROJECT_ROOT}/.env.${DEPLOYMENT_ENV}"
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Environment file ${ENV_FILE} not found. Copy .env.${DEPLOYMENT_ENV}.example and update values."
    fi
    
    # Create secrets from environment file
    kubectl create secret generic agrisense-secrets \
        --from-env-file="$ENV_FILE" \
        --namespace="$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply Kubernetes manifests
    if [[ -f "${PROJECT_ROOT}/k8s/${DEPLOYMENT_ENV}.yaml" ]]; then
        kubectl apply -f "${PROJECT_ROOT}/k8s/${DEPLOYMENT_ENV}.yaml"
        log_success "Kubernetes manifests applied"
    else
        log_error "Kubernetes manifest file k8s/${DEPLOYMENT_ENV}.yaml not found"
    fi
}

# Deploy monitoring stack
deploy_monitoring() {
    log "Deploying monitoring stack..."
    
    # Deploy Prometheus and Grafana if monitoring manifests exist
    if [[ -f "${PROJECT_ROOT}/k8s/monitoring.yaml" ]]; then
        kubectl apply -f "${PROJECT_ROOT}/k8s/monitoring.yaml"
        log_success "Monitoring stack deployed"
    else
        log_warning "Monitoring manifests not found - skipping monitoring deployment"
    fi
}

# Update deployment images
update_deployment_images() {
    log "Updating deployment images..."
    
    # Update main backend deployment
    kubectl set image deployment/agrisense-backend-blue \
        agrisense="${DOCKER_REGISTRY}/agrisense:${IMAGE_TAG}" \
        --namespace="$NAMESPACE"
    
    # Update Celery worker deployments
    kubectl set image deployment/celery-worker-data \
        celery-worker="${DOCKER_REGISTRY}/agrisense-celery:${IMAGE_TAG}" \
        --namespace="$NAMESPACE"
    
    kubectl set image deployment/celery-worker-ml \
        celery-worker="${DOCKER_REGISTRY}/agrisense-celery:${IMAGE_TAG}" \
        --namespace="$NAMESPACE"
    
    kubectl set image deployment/celery-beat \
        celery-beat="${DOCKER_REGISTRY}/agrisense-celery:${IMAGE_TAG}" \
        --namespace="$NAMESPACE"
    
    kubectl set image deployment/flower \
        flower="${DOCKER_REGISTRY}/agrisense-celery:${IMAGE_TAG}" \
        --namespace="$NAMESPACE"
    
    log_success "Deployment images updated"
}

# Wait for deployments to be ready
wait_for_deployments() {
    log "Waiting for deployments to be ready..."
    
    local deployments=(
        "agrisense-backend-blue"
        "celery-worker-data"
        "celery-worker-ml"
        "celery-beat"
        "flower"
        "redis"
    )
    
    for deployment in "${deployments[@]}"; do
        log "Waiting for deployment ${deployment}..."
        kubectl rollout status deployment/"$deployment" --namespace="$NAMESPACE" --timeout=600s
    done
    
    log_success "All deployments are ready"
}

# Run health checks
run_health_checks() {
    log "Running health checks..."
    
    # Get backend service endpoint
    BACKEND_SERVICE=$(kubectl get service agrisense-backend-service -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
    
    if [[ -n "$BACKEND_SERVICE" ]]; then
        # Port forward for health check
        kubectl port-forward service/agrisense-backend-service 8080:80 -n "$NAMESPACE" &
        PF_PID=$!
        sleep 5
        
        # Health check
        if curl -f http://localhost:8080/health > /dev/null 2>&1; then
            log_success "Backend health check passed"
        else
            log_error "Backend health check failed"
        fi
        
        # Clean up port forward
        kill $PF_PID 2>/dev/null || true
    else
        log_warning "Could not find backend service for health check"
    fi
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Create a temporary job for migrations
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: agrisense-migrations-$(date +%s)
  namespace: $NAMESPACE
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: migrations
        image: ${DOCKER_REGISTRY}/agrisense:${IMAGE_TAG}
        command: ["python", "-m", "alembic", "upgrade", "head"]
        envFrom:
        - secretRef:
            name: agrisense-secrets
  backoffLimit: 3
EOF
    
    log_success "Migration job created"
}

# Blue-Green deployment for production
blue_green_deployment() {
    if [[ "$DEPLOYMENT_ENV" == "production" ]]; then
        log "Performing blue-green deployment..."
        
        # Deploy to green environment
        kubectl set image deployment/agrisense-backend-green \
            agrisense="${DOCKER_REGISTRY}/agrisense:${IMAGE_TAG}" \
            --namespace="$NAMESPACE"
        
        # Scale up green deployment
        kubectl scale deployment agrisense-backend-green --replicas=3 --namespace="$NAMESPACE"
        
        # Wait for green deployment
        kubectl rollout status deployment/agrisense-backend-green --namespace="$NAMESPACE" --timeout=600s
        
        # Switch traffic to green
        kubectl patch service agrisense-backend-service \
            -p '{"spec":{"selector":{"version":"green"}}}' \
            --namespace="$NAMESPACE"
        
        # Scale down blue deployment after successful switch
        sleep 30
        kubectl scale deployment agrisense-backend-blue --replicas=0 --namespace="$NAMESPACE"
        
        log_success "Blue-green deployment completed"
    fi
}

# Cleanup old resources
cleanup_old_resources() {
    log "Cleaning up old resources..."
    
    # Remove completed jobs older than 24 hours
    kubectl delete jobs --field-selector=status.successful=1 \
        --namespace="$NAMESPACE" \
        --ignore-not-found=true
    
    # Remove old replica sets
    kubectl delete replicasets --field-selector=status.replicas=0 \
        --namespace="$NAMESPACE" \
        --ignore-not-found=true
    
    log_success "Cleanup completed"
}

# Backup before deployment
backup_before_deployment() {
    if [[ "$DEPLOYMENT_ENV" == "production" ]]; then
        log "Creating backup before deployment..."
        
        # Create backup job
        cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: agrisense-backup-$(date +%s)
  namespace: $NAMESPACE
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: backup
        image: ${DOCKER_REGISTRY}/agrisense:${IMAGE_TAG}
        command: ["python", "scripts/backup_database.py"]
        envFrom:
        - secretRef:
            name: agrisense-secrets
        volumeMounts:
        - name: backup-storage
          mountPath: /app/backups
      volumes:
      - name: backup-storage
        persistentVolumeClaim:
          claimName: backup-pvc
  backoffLimit: 1
EOF
        
        log_success "Backup job created"
    fi
}

# Rollback function
rollback_deployment() {
    log_error "Deployment failed. Initiating rollback..."
    
    if [[ "$DEPLOYMENT_ENV" == "production" ]]; then
        # Switch back to blue in case of failure
        kubectl patch service agrisense-backend-service \
            -p '{"spec":{"selector":{"version":"blue"}}}' \
            --namespace="$NAMESPACE"
        
        kubectl scale deployment agrisense-backend-blue --replicas=3 --namespace="$NAMESPACE"
        kubectl scale deployment agrisense-backend-green --replicas=0 --namespace="$NAMESPACE"
    else
        # Regular rollback
        kubectl rollout undo deployment/agrisense-backend-blue --namespace="$NAMESPACE"
    fi
    
    log_error "Rollback completed"
}

# Send notification
send_notification() {
    local status=$1
    local message=$2
    
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"AgriSense Deployment ${status}: ${message}\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
}

# Main deployment function
main() {
    local start_time=$(date +%s)
    
    log "Starting AgriSense deployment to ${DEPLOYMENT_ENV}..."
    log "Using image tag: ${IMAGE_TAG}"
    log "Using namespace: ${NAMESPACE}"
    
    # Trap for cleanup on failure
    trap 'rollback_deployment' ERR
    
    # Pre-deployment steps
    check_prerequisites
    create_namespace
    
    if [[ "${SKIP_BUILD:-false}" != "true" ]]; then
        build_and_push_images
    fi
    
    if [[ "$DEPLOYMENT_ENV" == "production" ]]; then
        backup_before_deployment
    fi
    
    # Main deployment
    deploy_configuration
    run_migrations
    
    if [[ "${SKIP_MONITORING:-false}" != "true" ]]; then
        deploy_monitoring
    fi
    
    update_deployment_images
    
    if [[ "$DEPLOYMENT_ENV" == "production" ]]; then
        blue_green_deployment
    else
        wait_for_deployments
    fi
    
    # Post-deployment steps
    run_health_checks
    cleanup_old_resources
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_success "Deployment completed successfully in ${duration} seconds!"
    send_notification "SUCCESS" "Deployment to ${DEPLOYMENT_ENV} completed in ${duration} seconds"
}

# Script usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --env ENVIRONMENT     Deployment environment (default: production)"
    echo "  -t, --tag IMAGE_TAG       Docker image tag (default: latest)"
    echo "  -r, --registry REGISTRY   Docker registry (default: ghcr.io/your-org)"
    echo "  --skip-build             Skip building and pushing images"
    echo "  --skip-monitoring        Skip monitoring stack deployment"
    echo "  --dry-run                Show what would be done without executing"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  DEPLOYMENT_ENV           Deployment environment"
    echo "  IMAGE_TAG                Docker image tag"
    echo "  DOCKER_REGISTRY          Docker registry URL"
    echo "  SLACK_WEBHOOK_URL        Slack webhook for notifications"
    echo ""
    echo "Examples:"
    echo "  $0 -e staging -t v1.2.3"
    echo "  $0 --env production --tag latest --skip-build"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            DEPLOYMENT_ENV="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -r|--registry)
            DOCKER_REGISTRY="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-monitoring)
            SKIP_MONITORING=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Dry run mode
if [[ "${DRY_RUN:-false}" == "true" ]]; then
    log "DRY RUN MODE - No changes will be made"
    log "Would deploy to environment: ${DEPLOYMENT_ENV}"
    log "Would use image tag: ${IMAGE_TAG}"
    log "Would use namespace: ${NAMESPACE}"
    exit 0
fi

# Run main deployment
main "$@"