import unittest as ut
import automata as fa


class FADualStateNodesTest(ut.TestCase):
    def setUp(self):
        self.node = fa.FANode(is_start=True, is_end=True, nid='StartAndEnd', label='StartAndEnd')
        self.automaton = fa.FA([self.node])

    def test_start_state_is_end_state(self):
        self.assertTrue(self.automaton.is_accepted(), 'Not accepted immediately when is_start node is is_end node')

    def test_unmatch_case(self):
        ret = self.automaton.move_next(' ')
        self.assertFalse(ret, 'Not failed when input is invalid')
        self.assertEqual(self.automaton.max_match, 0, 'Max match not 0')


class FAToDFATest(ut.TestCase):
    def setUp(self):
        self.node_start = fa.FANode(is_start=True, nid='start')
        self.node_a1 = fa.FANode(nid='a1')
        self.node_a2 = fa.FANode(nid='a2')
        self.node_a3 = fa.FANode(nid='a3')
        self.node_a4 = fa.FANode(nid='a4')
        self.node_end = fa.FANode(is_end=True, nid='end')
        self.node_start.point_to(None, 'a1')
        self.node_start.point_to(None, 'a3')
        self.node_a1.point_to('x', 'a2')
        self.node_a3.point_to('y', 'a4')
        self.node_a2.point_to(None, 'end')
        self.node_a4.point_to(None, 'end')
        self.automaton = fa.FA([
            self.node_start,
            self.node_a1,
            self.node_a2,
            self.node_a3,
            self.node_a4,
            self.node_end
        ])

    def test_to_dfa(self):
        self.automaton.to_dfa(new_fa=False, minimize=False)
        # fa.visualize.FADiGraph().from_fa(self.automaton).get_graph().render(view=True)
        self.assertTrue(len(self.automaton.nodes.values()) == 3, 'To DFA algorithm failed')

    def test_minimize(self):
        dfa = self.automaton.to_dfa(new_fa=True)
        self.assertTrue(dfa.is_dfa(), 'DFA Assert feature failed')
        dfa.minimize(new_fa=False)
        self.assertTrue(len(dfa.nodes.values()) == 2, 'DFA minimized failed')


if __name__ == '__main__':
    ut.main()
