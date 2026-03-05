### To run pytests, you need to port forward PostgreSQL port 5432 as well as the backend

    pip install -r tests/requirements-test.txt

    kubectl port-forward svc/primepass-primary 5432:5432

    kubectl port-forward svc/backend 5000:5000

    pytest -s