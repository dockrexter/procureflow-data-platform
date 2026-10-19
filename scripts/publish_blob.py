"""Publish a verified source batch to the separate source storage account."""
import argparse
from landing import land

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('batch')
    p.add_argument('--account', required=True)
    a = p.parse_args()
    print(land(a.batch, account=a.account, container='outbound'))
