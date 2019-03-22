from algorithms.HGS.message import HGSMessageAdapter, DefaultHGSMessageAdapter
from algorithms.IMGA.message import IMGAMessageAdapter, DefaultIMGAMessageAdapter
from algorithms.base.model import SubPopulation


def NSGAIIIIMGAMessageAdapter(driver):
    return DefaultIMGAMessageAdapter(driver)


def NSGAIIIHGSMessageAdapter(driver):
    return DefaultHGSMessageAdapter(driver)