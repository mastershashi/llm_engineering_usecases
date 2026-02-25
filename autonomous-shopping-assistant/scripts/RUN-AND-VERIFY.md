# Run and verify the app

## 1. Install and test (no servers)

```bash
cd autonomous-shopping-assistant
pip install -r requirements.txt
export PYTHONPATH=$(pwd) ENV=dev
python3 scripts/test_flow_inprocess.py
```

You should see:
- `[OK] External search + compare: ...`
- `[OK] StubLLM returns search_internet for 'Find running shoes'`
- `[OK] ProcessRequestUseCase: got bestDeal and cards`
- `All checks passed.`

If that fails, fix the reported error before starting services.

## 2. Start all 5 services

In **5 separate terminals** (from `autonomous-shopping-assistant`):

```bash
export PYTHONPATH=$(pwd) ENV=dev
uvicorn services.orchestration.main:app --port 8000 --reload
# Terminal 2:
uvicorn services.commerce.main:app      --port 8001 --reload
# Terminal 3:
uvicorn services.memory.main:app       --port 8002 --reload
# Terminal 4:
uvicorn services.agent.main:app        --port 8003 --reload
# Terminal 5:
uvicorn services.gateway.main:app       --port 8080 --reload
```

Or run all in one go (stop with Ctrl+C):

```bash
python3 scripts/run_all_dev.py
```

## 3. Verify it's working

1. **Health**
   ```bash
   curl http://localhost:8080/health
   ```
   Expected: `{"status":"ok","service":"gateway"}`

2. **Chat (search)**
   ```bash
   curl -X POST http://localhost:8080/v1/tenants/00000000-0000-0000-0000-000000000001/sessions \
     -H "Content-Type: application/json" \
     -d '{"message":{"type":"text","payload":{"text":"Find running shoes"}}}'
   ```
   Expected: JSON with `sessionId`, `reply.text`, `reply.cards` (list of offers), `reply.bestDeal`, `reply.reasoning`.

3. **UI**
   Open **http://localhost:8080** in a browser. Type "Find running shoes" and you should see product cards with store names and a "Best deal" recommendation.

If any step fails, check the terminal of the service that handles that request (orchestration for session, agent for tool calls, commerce for search/cart).
