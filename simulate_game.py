import requests
import random
import threading
import time

BASE_URL = "http://localhost:8000"

def simulate_team(team_index):
    team_name = f"Team_Sim_{team_index}"
    m1_name = f"Player1_{team_index}"
    m2_name = f"Player2_{team_index}"
    m1_prn = f"PRN1_{team_index}"
    m2_prn = f"PRN2_{team_index}"
    
    # 1. Login/Register
    print(f"[{team_name}] Logging in...")
    login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "team_name": team_name,
        "member_1_name": m1_name,
        "member_2_name": m2_name,
        "member_1_prn": m1_prn,
        "member_2_prn": m2_prn
    })
    
    if login_resp.status_code != 200:
        print(f"[{team_name}] Login failed: {login_resp.text}")
        return
        
    team_data = login_resp.json()
    team_id = team_data.get("team_id", team_data.get("id"))
    if not team_id:
        print(f"[{team_name}] Failed to get team_id from login response: {team_data}")
        return
        
    print(f"[{team_name}] Logged in successfully. Team ID: {team_id}")
    
    # 2. Round 1 Items
    print(f"[{team_name}] Fetching Round 1 items...")
    r1_items_resp = requests.get(f"{BASE_URL}/api/round1/items", params={"team_id": team_id})
    if r1_items_resp.status_code != 200:
        print(f"[{team_name}] Failed to get items: {r1_items_resp.text}")
        return
        
    items_data = r1_items_resp.json()
    if isinstance(items_data, list):
        items = items_data
    else:
        items = items_data.get("items", [])
        
    if not items:
        print(f"[{team_name}] No items found!")
        return
        
    # 3. Submit Round 1 Answers
    for item in items:
        item_id = item["id"]
        answer = random.choice(["PAST", "PRESENT", "FUTURE"])
        # print(f"[{team_name}] Submitting {answer} for item {item_id}...")
        sub_resp = requests.post(
            f"{BASE_URL}/api/round1/submit", 
            params={"team_id": team_id, "item_id": item_id, "answer": answer}
        )
        if sub_resp.status_code != 200:
            print(f"[{team_name}] Submit failed for item {item_id}: {sub_resp.text}")
            
    # 4. Finish Round 1
    print(f"[{team_name}] Finishing Round 1...")
    fin_resp = requests.post(f"{BASE_URL}/api/round1/finish", params={"team_id": team_id})
    if fin_resp.status_code != 200:
        print(f"[{team_name}] Finish failed: {fin_resp.text}")
        return
        
    # Skip Round 2
    
    # 5. Round 3 Start
    print(f"[{team_name}] Starting Round 3...")
    r3_start_resp = requests.post(f"{BASE_URL}/api/round3/start", json={"team_id": team_id})
    if r3_start_resp.status_code != 200:
        print(f"[{team_name}] Round 3 start failed: {r3_start_resp.text}")
        return
        
    # 6. Round 3 Submit
    print(f"[{team_name}] Submitting Round 3...")
    suspect = random.choice(["alpha", "beta", "gamma"])
    r3_submit_resp = requests.post(f"{BASE_URL}/api/round3/submit", json={
        "team_id": team_id,
        "selected_candidate_id": suspect,
        "selected_evidence_ids": []
    })
    
    if r3_submit_resp.status_code != 200:
        print(f"[{team_name}] Round 3 submit failed: {r3_submit_resp.text}")
        return
        
    print(f"[{team_name}] Successfully completed game! R3 verdict: {r3_submit_resp.json().get('is_correct')}")

def main():
    print("Clearing database...")
    clear_resp = requests.post(f"{BASE_URL}/api/admin/api/admin/clear-db", json={"password": "admin"})
    if clear_resp.status_code != 200:
        print(f"Failed to clear db: {clear_resp.text}")
        
    threads = []
    for i in range(1, 7):
        t = threading.Thread(target=simulate_team, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    print("All teams finished!")
    
    print("\nChecking leaderboard...")
    lb_resp = requests.get(f"{BASE_URL}/api/admin/api/admin/leaderboard")
    if lb_resp.status_code == 200:
        lb_data = lb_resp.json()
        print(f"Leaderboard fetched successfully. Top teams:")
        if isinstance(lb_data, list):
            teams = lb_data
        else:
            teams = lb_data.get("teams", [])
        for idx, team in enumerate(teams[:6]):
            print(f"{idx+1}. {team.get('team_name')} - Score: {team.get('total_score')} - Status: {team.get('status')}")
    else:
        print(f"Failed to fetch leaderboard: {lb_resp.text}")

if __name__ == '__main__':
    main()
