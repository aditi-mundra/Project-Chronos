import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_prn_valid_prefixes_and_length():
    valid_test_cases = [
        ("23000000001", "24000000002"),
        ("25000000003", "26000000004"),
        ("23123456789", "25987654321"),
        ("24999999999", "26111111111"),
    ]
    for idx, (prn1, prn2) in enumerate(valid_test_cases):
        res = client.post("/api/auth/login", json={
            "team_name": f"Valid PRN Team {idx}",
            "member_1_name": f"Member One {idx}",
            "member_2_name": f"Member Two {idx}",
            "member_1_prn": prn1,
            "member_2_prn": prn2
        })
        assert res.status_code == 200, f"Failed for valid PRNs {prn1}, {prn2}: {res.text}"
        data = res.json()
        assert "team_id" in data

def test_prn_invalid_prefixes():
    invalid_prefixes = ["21000000001", "22000000001", "27000000001", "19000000001", "99000000001"]
    for prn in invalid_prefixes:
        # Invalid Member 1
        res = client.post("/api/auth/login", json={
            "team_name": f"Invalid Prefix Team {prn}",
            "member_1_name": "Alice",
            "member_2_name": "Bob",
            "member_1_prn": prn,
            "member_2_prn": "24000000000"
        })
        assert res.status_code == 400
        assert "Member 1 PRN must be strictly numeric, exactly 11 digits long, and start with 23, 24, 25, or 26." in res.json()["detail"]

        # Invalid Member 2
        res2 = client.post("/api/auth/login", json={
            "team_name": f"Invalid Prefix Team 2 {prn}",
            "member_1_name": "Alice",
            "member_2_name": "Bob",
            "member_1_prn": "23000000000",
            "member_2_prn": prn
        })
        assert res2.status_code == 400
        assert "Member 2 PRN must be strictly numeric, exactly 11 digits long, and start with 23, 24, 25, or 26." in res2.json()["detail"]

def test_prn_invalid_lengths():
    # 10 digits
    res = client.post("/api/auth/login", json={
        "team_name": "Short PRN Team",
        "member_1_name": "Alice",
        "member_2_name": "Bob",
        "member_1_prn": "2312345678",
        "member_2_prn": "24123456789"
    })
    assert res.status_code == 400
    assert "Member 1 PRN must be strictly numeric, exactly 11 digits long" in res.json()["detail"]

    # 12 digits
    res2 = client.post("/api/auth/login", json={
        "team_name": "Long PRN Team",
        "member_1_name": "Alice",
        "member_2_name": "Bob",
        "member_1_prn": "23123456789",
        "member_2_prn": "241234567890"
    })
    assert res2.status_code == 400
    assert "Member 2 PRN must be strictly numeric, exactly 11 digits long" in res2.json()["detail"]

def test_prn_non_numeric():
    res = client.post("/api/auth/login", json={
        "team_name": "Alphanumeric PRN Team",
        "member_1_name": "Alice",
        "member_2_name": "Bob",
        "member_1_prn": "2312345678A",
        "member_2_prn": "24123456789"
    })
    assert res.status_code == 400
    assert "Member 1 PRN must be strictly numeric, exactly 11 digits long" in res.json()["detail"]

def test_prn_identical_members_rejected():
    res = client.post("/api/auth/login", json={
        "team_name": "Duplicate PRN Team",
        "member_1_name": "Alice",
        "member_2_name": "Bob",
        "member_1_prn": "23123456789",
        "member_2_prn": "23123456789"
    })
    assert res.status_code == 400
    assert "Member 1 and Member 2 must have distinct PRNs." in res.json()["detail"]
