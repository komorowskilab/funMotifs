"""
Created on Sep 26, 2022

@author: Mark Melzer

Test functions to check section 1 in funMotifsMain.py
"""

import argparse
import unittest
import difflib
import sys

sys.path.insert(1, '../src/')
import DataProcessing
import ProcessTFMotifs
import Utilities


class TestSection1(unittest.TestCase):

    def test_collect_all_data(self):
        """ Test without existing data directory """
        data_tracks = "./InputTestFilesSection1/DataTracks/CAGE_expr_per_peak_all_cells_promoters_enhancers.bed4,./InputTestFilesSection1/DataTracks/RoaDomainsAllGrouped.bed4,./InputTestFilesSection1/DataTracks/RoaLoopsAllGrouped.bed4,./InputTestFilesSection1/DataTracks/ReplicationDomains.bed4,./InputTestFilesSection1/DataTracks/*ChIP-seq.bed4,./InputTestFilesSection1/DataTracks/*_DNase-seq.bed4,./InputTestFilesSection1/DataTracks/*_ChromatinStates.bed4"
        all_chromatin_makrs_all_cells_combined_dir_path = './InputTestFilesSection1/chromatin_marks_all_cells_onlynarrowpeaks/'
        data_dir = DataProcessing.collect_all_data(all_chromatin_makrs_all_cells_combined_dir_path, data_tracks)
        # check if the created file is the expected output

        with open('./InputTestFilesSection1/chromatin_marks_all_cells_onlynarrowpeaks/chr10.bed', 'r') as a, open(
                './InputTestFilesSection1/CollectDataOutput', 'r') as b:
            differ = difflib.Differ()
            for line in differ.compare(a.readlines(), b.readlines()):
                self.assertNotEqual(line[0], '-')
                self.assertNotEqual(line[0], '+')
        return

    def test_retreive_TFFamilyName_for_motifNames(self):
        # TODO: create further working and not working tests (space-separated, self written column?)
        outcome = {'KEY1': ['KEY1', 'VALUE1'], 'KEY2': ['KEY2', '#VALUE2A', 'VALUE2B'],
                   'KEY3': ['KEY3', 'VALUE3A', 'VALUE3B'], 'KEY4': ['KEY4', '#VALUE4'],
                   'KEY5': ['KEY5', 'VALUE5A', 'VALUE5B']}
        TF_family_matches_file_test = "./InputTestFilesSection1/TFNames_motifNames_mapping_test"
        x = ProcessTFMotifs.retreive_TFFamilyName_for_motifNames(TF_family_matches_file_test)
        assert x == outcome
        # add return value to call this function in next one
        return x

    def test_get_expression_level_per_originType_per_TF(self):
        inputfile = \
            "./InputTestFilesSection1/GeneExp/GTEx_Analysis_test.gct"
        motifTFName_TFNames_matches_dict = self.test_retreive_TFFamilyName_for_motifNames()
        x = ProcessTFMotifs.get_expression_level_per_originType_per_TF(
            motifTFName_TFNames_matches_dict,
            normal_gene_expression_inputfile=inputfile,
            origin_gene_expression_values_outputfile=inputfile + "_perTissue_perTF",
            index_tissues_names_row_start=2,
            index_gene_names_col=1,
            index_gene_values_start=2,
            sep='\t', force_overwrite=True)
        exp_outcome = {"TissueA": {"KEY1": 0.0, "KEY2": "NaN", "KEY4": "NaN", "KEY3": 8.294, "KEY5": 0.0},
                       "TissueB": {"KEY1": 0.0, "KEY2": "NaN", "KEY4": "NaN", "KEY3": 7.283, "KEY5": 0.0},
                       "TissueC": {"KEY1": 0.0, "KEY2": "NaN", "KEY4": "NaN", "KEY3": 6.109, "KEY5": 0.0}}
        assert exp_outcome == x
        return x

    def test_retreive_key_values_from_dict_file(self):
        # use this file when testing this function only and use assert statements
        infile = "./InputTestFilesSection1/cell_names_to_consider_test.txt"
        # infile = "./InputTestFilesSection1/cell_names_to_consider.txt"
        output_dict = ['SWE', 'MEX', 'GER']
        output_rev = {'Sweden': 'SWE', 'Sverige': 'SWE', 'Mexico': 'MEX', 'Germany': 'GER'}
        x = Utilities.retreive_key_values_from_dict_file(
            infile,
            key_value_sep='=',
            values_sep=',')

        assert output_dict == x[0]
        assert output_rev == x[1]
        return Utilities.retreive_key_values_from_dict_file("./InputTestFilesSection1/cell_names_to_consider.txt", '=',
                                                            ',')

    def test_get_assay_cell_info(self):
        data_dir = "./InputTestFilesSection1/chromatin_marks_all_cells_onlynarrowpeaks/"
        matching_cell_name_representative_dict = self.test_retreive_key_values_from_dict_file()[1]
        tissues_with_gene_expression = list(self.test_get_expression_level_per_originType_per_TF().keys())
        x = DataProcessing.get_assay_cell_info(
            data_dir=data_dir,
            sep='\t',
            matching_rep_cell_names_dict=matching_cell_name_representative_dict,
            generated_dicts_output_file=data_dir + "generated_dicts.txt",
            tissues_with_gene_expression=tissues_with_gene_expression)

        with open('./InputTestFilesSection1/expected_generated_dicts.txt', 'r') as a, open(
                './InputTestFilesSection1/chromatin_marks_all_cells_onlynarrowpeaks/generated_dicts.txt', 'r') as b:
            differ = difflib.Differ()
            for line in differ.compare(a.readlines(), b.readlines()):
                self.assertNotEqual(line[0], '-')
                self.assertNotEqual(line[0], '+')
        return x

    def test_generate_cells_assays_matrix(self):
        _, cell_assays, _, _, assay_cells_datatypes = self.test_get_assay_cell_info()
        # use lines below if all alternative cell names need to be considered
        # cell_names1, cell_names2 = self.test_retreive_key_values_from_dict_file()
        # cell_names = cell_names1 + list(cell_names2.keys())
        x = DataProcessing.generate_cells_assays_matrix(cell_assays,
                                                        cell_names=self.test_retreive_key_values_from_dict_file()[0],
                                                        assay_cells_datatypes=assay_cells_datatypes,
                                                        tissues_with_gene_expression=list(
                                                            self.test_get_expression_level_per_originType_per_TF().keys()))
        print(x)

        expected_outcome = {'TissueA': {'TFExpr': 0.0}, 'TissueB': {'TFExpr': 0.0}, 'TissueC': {'TFExpr': 0.0},
                            'HepG2': {'FANTOM': 0.0}, 'GM12878': {'ContactingDomain': 0.0, 'LoopDomain': 0.0,
                                                                  'TFBinding': 0.0, 'NumOtherTFBinding': 0.0,
                                                                  'OtherTFBinding': 'NO', 'DNase-seq': 0.0,
                                                                  'ChromHMM': 'NO'}}

        assert expected_outcome == x
        return x

    def test_cell_to_tissue_matches(self):
        dict_input_file = "./InputTestFilesSection1/TissueCellMatches"
        x = Utilities.cell_to_tissue_matches(dict_input_file, key_value_sep='=', value_sep=',')
        y = {'MCF-7': 'Breast', 'T47D': 'Breast', 'HeLa-S3': 'Cervix', 'ME-180': 'Cervix', 'GM12878': 'Blood',
             'Colon - Sigmoid': 'Colon'}
        assert x == y

        return

if __name__ == '__main__':
    unittest.main()
