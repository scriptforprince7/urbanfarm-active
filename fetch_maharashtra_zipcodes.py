import indiapins
import json

def fetch_maharashtra_zipcodes():
    maharashtra_zipcodes = set()
    for zipcode in range(400000, 500000):
        try:
            pin_details = indiapins.matching(str(zipcode))
            for detail in pin_details:
                if detail['State'] == 'Maharashtra':
                    maharashtra_zipcodes.add(detail['Pincode'])
        except Exception as e:
            continue
    return list(maharashtra_zipcodes)

if __name__ == "__main__":
    maharashtra_zipcodes = fetch_maharashtra_zipcodes()
    with open('maharashtra_zipcodes.json', 'w') as f:
        json.dump(maharashtra_zipcodes, f)
    print(f"Fetched and stored {len(maharashtra_zipcodes)} Maharashtra zip codes.")
