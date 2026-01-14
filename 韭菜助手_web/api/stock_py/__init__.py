from .data.data_hushen300 import hushen300_manager
from .data.data_bond_yield import bond_yield_manager
from .data.data_gdp import china_gdp_manager
from .data.data_stock_market import china_stock_market_manager
from .data.data_cpi import china_cpi_manager
from .data.data_ppi import china_ppi_manager
from .data.data_money_supply import china_money_supply_manager
from .data.data_margin import margin_manager
from .data.data_listing_committee import listing_committee_manager
def initialize_data_managers():
    for m in [
        hushen300_manager,
        bond_yield_manager,
        china_gdp_manager,
        china_stock_market_manager,
        china_cpi_manager,
        china_ppi_manager,
        china_money_supply_manager,
        margin_manager,
        listing_committee_manager,
    ]:
        m.init_data()
def update_all_data():
    for m in [
        hushen300_manager,
        bond_yield_manager,
        china_gdp_manager,
        china_stock_market_manager,
        china_cpi_manager,
        china_ppi_manager,
        china_money_supply_manager,
        margin_manager,
        listing_committee_manager,
    ]:
        m.update_data()
