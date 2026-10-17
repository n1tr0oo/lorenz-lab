pipeline {
    agent any
    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timeout(time: 20, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    triggers { pollSCM('H/5 * * * *') }
    stages {
        stage('Checkout') {
            steps {
                deleteDir()
                checkout scm
                script {
                    env.SOURCE_SHA = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                    env.IMAGE_TAG = "lorenz-lab:${env.SOURCE_SHA.take(12)}-${env.BUILD_NUMBER}"
                    env.TEST_TAG = "lorenz-lab-tests:${env.SOURCE_SHA.take(12)}-${env.BUILD_NUMBER}"
                    env.TEST_CONTAINER = "lorenz-tests-${env.BUILD_NUMBER}"
                    env.CD_CONTAINER = "lorenz-demo-${env.BUILD_NUMBER}"
                }
                sh 'mkdir -p reports results'
            }
        }
        stage('Unit tests') {
            steps {
                sh '''docker build --target test --build-arg SOURCE_COMMIT="$SOURCE_SHA" -t "$TEST_TAG" .
                    status=0
                    docker run --name "$TEST_CONTAINER" "$TEST_TAG" || status=$?
                    docker cp "$TEST_CONTAINER:/reports/." reports/
                    exit "$status"'''
            }
            post {
                always {
                    junit testResults: 'reports/junit.xml', allowEmptyResults: false
                    sh 'docker rm -f "$TEST_CONTAINER" >/dev/null 2>&1 || true'
                }
            }
        }
        stage('Build image') {
            steps {
                sh '''docker build --target runtime --build-arg SOURCE_COMMIT="$SOURCE_SHA" -t "$IMAGE_TAG" .
                    docker image inspect "$IMAGE_TAG" > reports/image-inspect.json'''
            }
        }
        stage('Repeat experiment') {
            steps {
                sh '''for run in 1 2; do
                        name="lorenz-run-$BUILD_NUMBER-$run"
                        docker run --name "$name" --tmpfs /tmp:rw,size=64m --cap-drop ALL \
                            --security-opt no-new-privileges "$IMAGE_TAG"
                        mkdir -p "results/run-$run"
                        docker cp "$name:/data/default/." "results/run-$run/"
                        docker rm "$name"
                    done
                    python3 tools/verify_runs.py results/run-1 results/run-2 "$SOURCE_SHA" > reports/repeatability.json
                    cat reports/repeatability.json'''
            }
        }
        stage('Deploy test site') {
            steps {
                sh '''docker run -d --name "$CD_CONTAINER" --read-only --tmpfs /tmp \
                        --cap-drop ALL --security-opt no-new-privileges \
                        -p 127.0.0.1:8090:8000 --entrypoint python "$IMAGE_TAG" \
                        -m http.server --bind 0.0.0.0 8000 --directory /app/docs
                    python3 - <<'PY'
import json, time, urllib.request
for attempt in range(30):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8090/', timeout=3) as response:
            body = response.read().decode()
            assert response.status == 200 and 'Lorenz' in body
        break
    except (OSError, AssertionError):
        time.sleep(1)
else:
    raise SystemExit('test deployment did not become ready')
with open('reports/deployment.json', 'w') as handle:
    json.dump({'http_status': 200, 'title_contains_lorenz': True,
               'endpoint': 'http://127.0.0.1:8090/',
               'scope': 'temporary test service on the CI runner'}, handle, indent=2)
PY'''
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'reports/**,results/**', fingerprint: true, allowEmptyArchive: true
        }
        cleanup {
            sh '''docker rm -f "$TEST_CONTAINER" >/dev/null 2>&1 || true
                for run in 1 2; do docker rm -f "lorenz-run-$BUILD_NUMBER-$run" >/dev/null 2>&1 || true; done'''
        }
    }
}
