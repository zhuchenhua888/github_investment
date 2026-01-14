import akshare as ak

def fetch_qdii_data():
    # Fetch QDII index data
    qdii_index_data = ak.qdii_e_index_jsl()
    print("QDII Index Data:")
    print(qdii_index_data["净值日期"])
    
    qdii_index_data_excel = "qdii数据.xlsx"
    qdii_index_data.to_excel(qdii_index_data_excel, index=True)

    # Fetch QDII commodity data
    qdii_comm_data = ak.qdii_e_comm_jsl()
    print("\nQDII Commodity Data:")
    print(qdii_comm_data)

if __name__ == "__main__":
    fetch_qdii_data()