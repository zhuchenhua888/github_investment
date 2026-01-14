import akshare as ak

def fetch_qdii_data():
    qdii_index_data = ak.qdii_a_index_jsl()
    
    qdii_index_data_excel = "数据-亚洲指数数据.xlsx"
    qdii_index_data.to_excel(qdii_index_data_excel, index=True)

if __name__ == "__main__":
    fetch_qdii_data()