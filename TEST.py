import json
import requests
import os

# Definieer je Pipedrive- en Notion-API-URL's en tokens
pipedrive_api_url = "https://newmonday-sandbox.pipedrive.com/api/v1"
notion_api_url = "https://api.notion.com/v1"
pipedrive_token = os.environ.get("PIPEDRIVE_TOKEN")
notion_token = os.environ.get("NOTION_TOKEN")
notion_database_id = "ce40cf1499e74454869f8047c97a66e1"
notion_version = "2022-06-28"

# Functie om gegevens van Pipedrive op te halen
def get_pipedrive_data():
    url = f"{pipedrive_api_url}/deals"
    params = {"api_token": pipedrive_token}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()["data"]
    else:
        print("Fout bij het ophalen van Pipedrive-gegevens:", response.text)
        return None

# Functie om een bestaande deal in Notion bij te werken
def update_notion_deal(page_id, updated_data):
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": notion_version,
    }
    url = f"{notion_api_url}/pages/{page_id}"
    response = requests.patch(url, headers=headers, json=updated_data)
    if response.status_code == 200:
        print(f"Deal met ID '{page_id}' succesvol bijgewerkt in Notion.")
        return True
    else:
        print(f"Fout bij het bijwerken van deal in Notion: {response.text}")
        return False

# Functie om gegevens naar Notion te sturen en bestaande deals bij te werken indien nodig
def send_to_notion(deals):
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": notion_version,
    }
    for deal in deals:
        deal_id = deal.get("id")
        title = deal.get("title")
        value = deal.get("value")
        organization_name = deal.get("org_name")
        person_name = deal.get("person_name")
        expected_close_date = deal.get("expected_close_date")
        status = deal.get("status")
        image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Pipedrive_Logo.svg/2560px-Pipedrive_Logo.svg.png"  # URL van de afbeelding toegevoegd

        if title:
            # Controleren of de deal al bestaat in Notion
            page_id = get_notion_page_id(deal_id)
            if page_id:
                # Deal bestaat al, update de deal
                updated_data = {
                    "properties": {
                        "ID": {"number": deal_id},
                        "Titel": {"title": [{"text": {"content": title}}]},
                        "Waarde": {"number": value},
                        "Organisatie": {"rich_text": [{"text": {"content": organization_name}}]},
                        "Contactpersoon": {"rich_text": [{"text": {"content": person_name}}]},
                        "Verwachte sluitingsdatum": {"date": {"start": expected_close_date}},
                        "Status": {"select": {"name": status}}
                    },
                    "cover": {
                        "type": "external",
                        "external": {
                            "url": image_url
                        }
                    }
                }
                success = update_notion_deal(page_id, updated_data)
                if not success:
                    return False
            else:
                # Deal bestaat nog niet, maak een nieuwe deal aan
                data = {
                    "parent": {"database_id": notion_database_id},
                    "properties": {
                        "ID": {"number": deal_id},
                        "Titel": {"title": [{"text": {"content": title}}]},
                        "Waarde": {"number": value},
                        "Organisatie": {"rich_text": [{"text": {"content": organization_name}}]},
                        "Contactpersoon": {"rich_text": [{"text": {"content": person_name}}]},
                        "Verwachte sluitingsdatum": {"date": {"start": expected_close_date}},
                        "Status": {"select": {"name": status}}
                    },
                    "cover": {
                        "type": "external",
                        "external": {
                            "url": image_url
                        }
                    }
                }
                response = requests.post(f"{notion_api_url}/pages", headers=headers, json=data)
                if response.status_code != 200:
                    print(f"Fout bij het sturen van deal naar Notion: {response.text}")
                    return False
        else:
            print("Geen titel gevonden voor deal:", deal)
    return True

# Functie om te controleren of een deal al bestaat in Notion
def get_notion_page_id(deal_id):
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": notion_version,
    }
    url = f"{notion_api_url}/databases/{notion_database_id}/query"
    data = {
        "filter": {
            "property": "ID",
            "number": {
                "equals": deal_id
            }
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        results = response.json()["results"]
        if results:
            return results[0]["id"]
        else:
            return None
    else:
        print(f"Fout bij het controleren van deal in Notion: {response.text}")
        return None

# Hoofdscript
if __name__ == "__main__":
    pipedrive_data = get_pipedrive_data()
    if pipedrive_data:
        success = send_to_notion(pipedrive_data)
        if success:
            print("Deals succesvol naar Notion gestuurd.")
        else:
            print("Er is een fout opgetreden bij het sturen van deals naar Notion.")
