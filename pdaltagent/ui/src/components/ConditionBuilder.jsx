import { useState } from 'react';
import {
  Box,
  Text,
  Textarea,
} from '@chakra-ui/react';

import parser from '../util/parser';

import Condition from './Condition';

const ConditionBuilder = ({
  condition,
  setCondition,
}) => {

  const [conditionHint, setConditionHint] = useState('');

  return (
    <Box>
      <Textarea
        isInvalid={!condition || Object.keys(condition).length === 0}
        placeholder="Enter a BPQL expression"
        onChange={(e) => {
          try {
            const newCondition = parser.parse(e.target.value);
            setCondition(newCondition);
            setConditionHint('');
          } catch (e) {
            setCondition({});
            setConditionHint(e.message);
          }
        }}
      />
      {conditionHint && <Text fontSize="sm" fontStyle="italic" color="red.500">{conditionHint}</Text>}
      <Condition condition={condition} />
    </Box>
  );
}

export default ConditionBuilder;