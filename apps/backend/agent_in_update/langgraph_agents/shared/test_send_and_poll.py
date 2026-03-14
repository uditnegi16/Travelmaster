# test_send_and_poll.py
import asyncio
import uuid
import httpx

BASE_URL = "http://localhost:10002/"

async def jsonrpc_post(method: str, params: dict, rpc_id: str = None):
    payload = {
        "jsonrpc": "2.0",
        "id": rpc_id or str(uuid.uuid4()),
        "method": method,
        "params": params,
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(BASE_URL, json=payload, timeout=30.0)
        r.raise_for_status()
        return r.json()

async def send_message_and_poll(text: str, context_id: str = "explore_test_1"):
    msg_id = f"msg-{uuid.uuid4().hex[:8]}"
    params = {
        "message": {
            "role": "user",
            "parts": [{"text": text}],
            "messageId": msg_id,
            "contextId": context_id,
        }
    }
    print("Sending message...")
    resp = await jsonrpc_post("message/send", params, rpc_id="send-1")
    print("send response:", resp)
    task_id = None
    if resp.get("result"):
        task_id = resp["result"].get("taskId") or resp["result"].get("id")
    if not task_id:
        print("No taskId in response; aborting.")
        return

    print("Polling task:", task_id)
    for i in range(20):
        resp2 = await jsonrpc_post("tasks/get", {"id": task_id}, rpc_id=f"poll-{i}")
        print(f"poll {i}:", resp2.get("result", {}).get("state"))
        if resp2.get("result", {}).get("state") == "completed":
            artifacts = resp2["result"].get("artifacts", [])
            print("Artifacts:", artifacts)
            break
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(send_message_and_poll("Find top attractions in Goa for 3 days family trip"))
