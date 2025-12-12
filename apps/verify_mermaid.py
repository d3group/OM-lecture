import base64
import textwrap
import requests

def check_mermaid():
    mermaid_code = textwrap.dedent("""
    graph LR
        subgraph L1 [Line 1: Granulation and Blending]
            direction LR
            Weighing --> Granulation --> Drying --> Blending
        end
        
        subgraph L2 [Line 2: Tablet Line (Compression and Coating)]
            direction LR
            Press[Tablet Press] --> Coater
        end
        
        subgraph L3 [Line 3: Packaging Lines]
            direction LR
            Blistering --> Cartoning --> Insertion[Leaflet Insertion]
        end
        
        style L2 fill:#f9f,stroke:#333,stroke-width:2px
    """).strip()

    graphbytes = mermaid_code.encode("utf8")
    base64_bytes = base64.b64encode(graphbytes)
    base64_string = base64_bytes.decode("ascii")
    url = f"https://mermaid.ink/img/{base64_string}"
    
    print(f"Generated URL: {url}")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print("Response:", response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_mermaid()
