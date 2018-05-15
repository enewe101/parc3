from unittest import main, TestCase
from collections import defaultdict
import parc3
import t4k


class TestReadAllAnnotations(TestCase):

    def test_read_all_annotations(self):
        dataset = parc3.annotation_merging.read_bnp_pronoun_dataset(
            skip=0,limit=20)
        print len(dataset)



class TestMergingPropbankVerbs(TestCase):

    def setUp(self):
        self.propbank_verbs_by_doc = (
            parc3.annotation_merging.read_propbank_verbs())

    def get_test_docs(self, doc_id):
        parc_doc = parc3.data.load_parc_doc(
            doc_id, include_nested=False)
        propbank_verbs = self.propbank_verbs_by_doc[doc_id]
        return parc_doc, propbank_verbs

    def test_several_docs_for_propbank_merging(self):
        for doc_id in [13, 17, 23, 29, 31, 37]:
            self.do_test_one_doc_for_propbank_merging(doc_id)


    MAX_DISTANCE_FOR_TOKEN_MATCH = 10
    def do_test_one_doc_for_propbank_merging(self, doc_id):

        parc_doc, propbank_verbs = self.get_test_docs(doc_id)
        parc3.annotation_merging.merge_propbank_verbs(
            parc_doc, propbank_verbs)

        for verb_id, (sentence_id,token_id,lemma) in enumerate(propbank_verbs):
            matched_token = parc_doc.annotations['propbank_verbs'][verb_id]
            matched_lemma = matched_token['lemma']
            matched_location = parc_doc.absolutize(matched_token['token_span'])
            matched_abs_id = matched_location[0][1]
            expected_location = parc_doc.absolutize(
                [(sentence_id, token_id, token_id + 1)])
            expected_location_abs_id = expected_location[0][1]
            distance = matched_abs_id - expected_location_abs_id
            self.assertEqual(lemma, matched_lemma)
            self.assertTrue(abs(distance) < self.MAX_DISTANCE_FOR_TOKEN_MATCH)



class TestTokenSpan(TestCase):

    def test_bad_span(self):
        with self.assertRaises(ValueError):
            parc3.spans.TokenSpan([(0, 0, 0)])
        with self.assertRaises(ValueError):
            parc3.spans.TokenSpan([(0, 1, 0)])
        with self.assertRaises(ValueError):
            parc3.spans.TokenSpan(single_range=(0, 0, 0))
        with self.assertRaises(ValueError):
            parc3.spans.TokenSpan(single_range=(0, 1, 0))
        with self.assertRaises(ValueError):
            parc3.spans.TokenSpan([(0, 1, 0)], absolute=True)
        with self.assertRaises(ValueError):
            parc3.spans.TokenSpan([(None, 1, 0)])
        with self.assertRaises(ValueError):
            parc3.spans.TokenSpan(single_range=(0,1))


    def test_consolidation(self):

        # Consolidation when one span is adjacent to another
        t1 = parc3.spans.TokenSpan([(0,0,1), (0,1,2)])
        t2 = parc3.spans.TokenSpan([(0,0,2)])
        self.assertEqual(t1, t2)

        # Consolidating when one span subsumes another
        t1 = parc3.spans.TokenSpan([(0,0,2), (0,1,3)])
        t2 = parc3.spans.TokenSpan([(0,0,3)])
        self.assertEqual(t1, t2)

        # Consolidation of unordered ranges works, and equality is maintained.
        t1 = parc3.spans.TokenSpan([(0,1,2), (0,0,1)])
        t2 = parc3.spans.TokenSpan([(0,0,2)])
        self.assertEqual(t1, t2)

        # Equality is not affected by order.
        t1 = parc3.spans.TokenSpan([(0,2,3), (0,0,1)])
        t2 = parc3.spans.TokenSpan([(0,0,1), (0,2,3)])
        self.assertEqual(t1, t2)


    def test_good_span(self):
        parc3.spans.TokenSpan(single_range=(0,0,1))
        parc3.spans.TokenSpan(single_range=(0,1), absolute=True)
        parc3.spans.TokenSpan(single_range=(None,0,1), absolute=True)


    def test_adding_ranges(self):

        # if `absolute=False`, ranges must have integer sentence_id
        span = parc3.spans.TokenSpan()
        with self.assertRaises(ValueError):
            span.append((None, 0, 1))
        span.append((0,0,1))
        self.assertEqual(span.get_single_range(), (0,0,1))

        # If `absolute=True`, appended ranges must have `sentence_id=None`
        span = parc3.spans.TokenSpan(absolute=True)
        span.append((None,0,1))
        self.assertEqual(span.get_single_range(), (None,0,1))
        with self.assertRaises(ValueError):
            span.append((0, 0, 1))

        # If `absolute=True`, appending multiple ranges that have
        # `sentence_id=None`.  Raise value error if `sentence_id` is an `int`
        span = parc3.spans.TokenSpan(absolute=True)
        span.extend([(None, 0,1), (None, 1,5)])
        self.assertEqual(span.get_single_range(), (None, 0,5))
        with self.assertRaises(ValueError):
            span.extend([(0, 0, 1), (None, 1, 5)])

        # If `absolute=True`, appending multiple ranges that have
        # `sentence_id=None`.  Raise value error if `sentence_id` is an `int`
        span = parc3.spans.TokenSpan()
        span.extend([(0, 0, 1), (0, 1, 5)])
        self.assertEqual(span.get_single_range(), (0, 0, 5))
        with self.assertRaises(ValueError):
            span.extend([(0, 0, 1), (None, 1, 5)])


    def test_len(self):
        empty_span = parc3.spans.TokenSpan()
        self.assertEqual(len(empty_span), 0)
        span_with_overlaps = parc3.spans.TokenSpan(
            [(0,3), (1,4)], absolute=True)
        self.assertEqual(len(span_with_overlaps), 4)




class TestReadParcFile(TestCase):

    # TODO: test token splitting

    def setUp(self):
        self.doc = self.get_test_doc()


    def get_test_doc(self, include_nested=True):
        first_interesting_article = 3
        path = parc3.data.get_parc_path(first_interesting_article)
        xml = open(path).read()
        return parc3.parc_reader.read_parc_file(
            xml, include_nested=include_nested)


    def test_num_attributions(self):
        """Ensure the correct number of attributions is found for the file."""
        num_attributions = len(self.doc.annotations['attributions'])
        expected_num_attributions = 13
        condition = num_attributions == expected_num_attributions,
        self.assertTrue(condition, 'incorrect number of attributions found')


    def test_attribution_spans_have_correct_tokens(self):
        """
        Ensure that a given attribution has the correct tokens in its
        source, cue, and content spans.
        """
        annotation_id = 'wsj_0003_Attribution_relation_level.xml_set_1'
        annotation = self.doc.annotations['attributions'][annotation_id]

        # Check that the source span and source text is correct
        expected_source_token_span = [(0,33,34)]
        self.assertEqual(annotation['source'], expected_source_token_span)

        expected_source_text = "researchers"
        found_source_text = self.doc.get_tokens(annotation['source']).text()
        self.assertEqual(found_source_text, expected_source_text)

        # Check that the cue span and cue text is correct
        expected_cue_token_span = [(0,34,35)]
        self.assertEqual(annotation['cue'], expected_cue_token_span)

        found_cue_text = self.doc.get_tokens(annotation['cue']).text()
        expected_cue_text = 'reported'
        self.assertEqual(found_cue_text, expected_cue_text)

        # Check that the content span and content text is correct
        expected_content_token_span = [(0,0,32)]
        self.assertEqual(annotation['content'], expected_content_token_span)

        found_content_text = self.doc.get_tokens(annotation['content']).text()
        expected_content_text = (
            "A form of asbestos once used to make Kent cigarette filters has "
            "caused a high percentage of cancer deaths among a group of workers"
            " exposed to it more than 30 years ago"
        )
        self.assertEqual(found_content_text, expected_content_text)


    def test_token_reference_to_attributions(self):

        found_token_references = defaultdict(
            lambda: {'source':set(), 'cue':set(), 'content':set()}
        )

        # First, iterate through all the tokens, and accumulate all those that
        # refer to attributions, according to which attribution / role they
        # reference.
        for token_id, token in enumerate(self.doc.tokens):
            for attribution in token['attributions']:
                for role in attribution['roles']:
                    attr_id = attribution['id']
                    found_token_references[attr_id][role].add(token_id)

        # Check that we got the complete set of attributions by accumulating
        # them from token references.
        self.assertEqual(
            found_token_references.keys(),
            self.doc.annotations['attributions'].keys()
        )

        # Now, go through each attribution, and check that we got all the same
        # tokens for each role in each attribution by accumulating them from
        # token references.
        attributions = self.doc.annotations['attributions']
        for attribution_id, attribution in attributions.items():
            for role in attribution.ROLES:
                token_ids = {
                    t['abs_id'] for t in self.doc.get_tokens(attribution[role])
                }
                self.assertEqual(
                    found_token_references[attribution_id][role],
                    token_ids, 
                )

    def test_exclude_nested(self):
        expected_num_nested = 3
        num_nested = len([
            key for key in 
            self.doc.annotations['attributions'].keys()
            if 'Nested' in key
        ])
        self.assertEqual(num_nested, expected_num_nested)

        doc_without_nested = self.get_test_doc(include_nested=False)
        excluded = (
            set(self.doc.annotations['attributions'].keys())
            - set(doc_without_nested.annotations['attributions'].keys())
        )
        self.assertEqual(len(excluded), expected_num_nested)
        self.assertTrue(all('Nested' in attr_id for attr_id in excluded))


    def test_tokens_pos_tags(self):
        found_pos = [t['pos'] for t in self.doc.get_sentence_tokens(1)]
        expected_pos = [
            'DT', 'NN', 'NN', 'COLON', 'NN', 'COLON', 'VBZ', 'RB', 'JJ', 'IN', 
            'PRP', 'VBZ', 'DT', 'NNS', 'COLON', 'IN', 'RB', 'JJ', 'NNS', 'TO', 
            'PRP', 'VBG', 'NNS', 'WDT', 'VBP', 'RP', 'NNS', 'JJ', 'COLON', 
            'NNS', 'VBD', 'PKT'
        ]
        condition = found_pos == expected_pos
        self.assertEqual(found_pos, expected_pos)


    def test_constituency_parse_tree_structure(self):
        """
        Ensure that the constituent tree is correct.
        """
        # Check that a DFS yields the correct sequence of constituents
        constituent = self.doc.sentences[0]
        found_dfs_sequence = [
            (depth, node['constituent_type']) 
            for depth, node in 
            parc3.spans.get_dfs_constituents(constituent)
        ]
        expected_dfs_sequence = [
            (0, u's'), (1, u's-tpc-1'), (2, u'np-sbj'), (3, u'np'), (4, u'np'),
            (5, 'token'), (5, 'token'), (4, u'pp'), (5, 'token'), (5, u'np'),
            (6, 'token'), (3, u'rrc'), (4, u'advp-tmp'), (5, 'token'),
            (4, u'vp'), (5, 'token'), (5, u's-clr'), (6, u'vp'), (7, 'token'),
            (7, u'vp'), (8, 'token'), (8, u'np'), (9, 'token'), (9, 'token'),
            (9, 'token'), (2, u'vp'), (3, 'token'), (3, u'vp'), (4, 'token'),
            (4, u'np'), (5, u'np'), (6, 'token'), (6, 'token'), (6, 'token'),
            (5, u'pp'), (6, 'token'), (6, u'np'), (7, 'token'), (7, 'token'),
            (5, u'pp-loc'), (6, 'token'), (6, u'np'), (7, u'np'), (8, 'token'),
            (8, 'token'), (7, u'pp'), (8, 'token'), (8, u'np'), (9, u'np'),
            (10, 'token'), (9, u'rrc'), (10, u'vp'), (11, 'token'),
            (11, u'pp-clr'), (12, 'token'), (12, u'np'), (13, 'token'),
            (11, u'advp-tmp'), (12, u'np'), (13, u'qp'), (14, 'token'),
            (14, 'token'), (14, 'token'), (13, 'token'), (12, 'token'),
            (1, 'token'), (1, u'np-sbj'), (2, 'token'), (1, u'vp'),
            (2, 'token'), (1, 'token')
        ]
        self.assertEqual(found_dfs_sequence, expected_dfs_sequence)


    def test_constituency_token_spans(self):
        """
        Test that sentence constituents are still absolutely addressed, and 
        that all other constituents have been converted to sentence-relative 
        addressing.
        """
        
        # Choose anything except the first sentence.  We need to make sure that 
        # the constituents' token_spans are addressed relative to the start of
        # the sentence
        TEST_SENTENCE_INDEX = 1

        # First check that the sentence constituent has correct absolute token
        # span
        found_token_span = self.doc.sentences[TEST_SENTENCE_INDEX]['token_span']
        sent_abs_start, sent_abs_end = 36, 68
        expected_token_span = [(None, sent_abs_start, sent_abs_end)]
        self.assertEqual(found_token_span, expected_token_span)

        
        # Now check that all other constituents have correct sentence-relative
        # token spans
        nodes_in_dfs_order = parc3.spans.get_dfs_constituents(
            self.doc.sentences[TEST_SENTENCE_INDEX])

        max_end = t4k.Max()

        past_first_token = False
        for depth, node in nodes_in_dfs_order:

            if depth == 0:
                continue

            self.assertTrue(node['token_span'].is_single_range())
            sentence_id, start, end = node['token_span'][0]
            max_end.add(end)

            last_end = None
            #print depth, node['constituent_type']
            #print 'start, end\t', start, end, last_end

            # All token_spans should be addressed to the test sentence's ID
            self.assertEqual(sentence_id, TEST_SENTENCE_INDEX)

            # The first constituents and tokens should have an index of zero
            if not past_first_token:
                self.assertEqual(start, 0)

            for child in parc3.spans.get_constituency_children(node):
                self.assertTrue(child['token_span'].is_single_range())
                token_span = child['token_span'][0]
                child_sentence_id, child_start, child_end = token_span
                self.assertEqual(child_sentence_id, sentence_id)

                # One child should pick up where the preceeding child left off
                # (Except for the first child, which has no preceeding child)
                if last_end is not None:
                    self.assertEqual(child_start, last_end)

                self.assertTrue(child_end <= end)
                last_end = child_end
                #print ' '.join(t4k.strings([],
                #    '\tchild_start, child_end, last_end\t',
                #    child_start, child_end, last_end
                #))

            if last_end is not None:
                #print 'did final child line up?\t', last_end, end
                self.assertEqual(last_end, end)

            if node['constituent_type'] == 'token':
                past_first_token = True

        self.assertEqual(max_end.max_key(), sent_abs_end - sent_abs_start)
        


if __name__ == '__main__':
    main()
