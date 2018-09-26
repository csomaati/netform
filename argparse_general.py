#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Altalanos argparse module, bizonyos parametereke
# altalanos kezelesehez
# Optimalis esetben minden argparse ebbol inicializalja
# magat, es ehhez ad hozza uj parametereket, vagy ir felul
# szukseg eseten meglevoeket

import argparse

commonParams = {
    "epilog": "Contact: csoma@tmit.bme.hu, gulyas@tmit.bme.hu",
    "formatter_class": argparse.ArgumentDefaultsHelpFormatter,
    "fromfile_prefix_chars": "@",
    "conflict_handler": "resolve"
}

desc = "Common parameters for all argument parser used in netform module",
commonParser = argparse.ArgumentParser(
    description=desc, add_help=False, **commonParams)

commonParser.add_argument(
    '--progressbar',
    action='store_true',
    help='Display a progressbar if possible')

commonParser.add_argument(
    '--verbose',
    '-v',
    action='count',
    default=0,
    help='Set the level of verbosity. 0: ERROR, 1: WARNING, 2: INFO, 3: DEBUG')

commonParser.add_argument(
    '--lower-bound',
    '-lb',
    type=int,
    default=0,
    dest='lb',
    help='Set the lower bound for the given dataset. Start multiple process with different lower and upper bound values to use all processore cores.'
)
commonParser.add_argument(
    '--upper-bound',
    '-ub',
    type=int,
    default=-1,
    dest='ub',
    help='Use this together with lowerbound parameter')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(parents=[commonParser, ], **commonParams)
    parser.parse_args()
