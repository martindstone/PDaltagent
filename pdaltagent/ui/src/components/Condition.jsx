import {
  Box,
  Flex,
  Tag,
  Text,
} from '@chakra-ui/react';

import { IconContext } from "react-icons";
import { VscRegex } from "react-icons/vsc";

const Identifier = ({identifier}) => {
  return (
    <Tag m={1} size="md" variant="solid" colorScheme="blue">
      {identifier}
    </Tag>
  )
}

const Operand = ({operand}) => {
  if (typeof operand === 'object') {
    if (operand.type === 'regex') {
      const value = operand.value;
      return (
        <Tag m={1} size="md" variant="solid" colorScheme="purple">
          {value}
          <Box ml={1} p={1} bgColor="white" opacity="50%" borderRadius="full">
            <IconContext.Provider value={{color: 'purple', size: '0.75em'}}>
              <VscRegex />
            </IconContext.Provider>
          </Box>
        </Tag>
      );
    } else if (operand.type === 'formal-regex') {
      const value = operand.value;
      return (
        <Tag m={1} size="md" variant="solid" colorScheme="red">
          {value}
          <Box ml={1} p={1} bgColor="white" opacity="50%" borderRadius="full">
            <IconContext.Provider value={{color: 'red', size: '0.75em'}}>
              <VscRegex />
            </IconContext.Provider>
          </Box>
        </Tag>
      );
    } else {
      return (
        <Tag m={1} size="md" variant="solid" colorScheme="green">
          {JSON.stringify(operand)}
        </Tag>
      );
    }
  } else {
    return (
      <Tag m={1} size="md" variant="solid" colorScheme="green">
        {operand}
      </Tag>
    );
  }
}

const Operator = ({operator}) => {
  return (
    <Tag variant="ghost">
      {operator}
    </Tag>
  );
}

const Condition = ({condition}) => {
  // condition should be an object with only one key,
  // the operator, and the value as the operands. Operators
  // are '=', '!=', 'IN', 'NOT IN'. Also there are group operators
  // 'AND', 'OR'. Group operators have an array of conditions as
  // their operands.

  // get the operator
  const operator = Object.keys(condition)[0];
  // get the operands
  const operands = condition[operator];

  // if the operator is a group operator
  if (['AND', 'OR'].includes(operator)) {
    return (
      <Tag m={1} shadow="sm" variant="solid" bgColor={(operator == 'AND') ? 'blue.300' : 'green.300'}>
        <Flex wrap="wrap">
          <Text m={1}>
            {operator}:
          </Text>
          {operands.map((op, i) => (
            <Condition key={i} condition={op} />
          ))}
        </Flex>
      </Tag>
    );
  }
  if (['IN', 'NOT IN'].includes(operator)) {
    return (
      <Tag m={1} shadow="sm" variant="solid" bgColor="gray.500">
        <Flex wrap="wrap">
          <Identifier identifier={operands[0]} />
          <Operator operator={operator} />
          {operands[1].map((op, i) => (
            <Operand key={i} operand={op} />
          ))}
        </Flex>
      </Tag>
    );
  }
  if (['=', '!='].includes(operator)) {
    return (
      <Tag m={1} shadow="sm" variant="solid" bgColor="gray.500">
        <Flex wrap="wrap">
          <Identifier identifier={operands[0]} />
          <Operator operator={operator} />
          <Operand operand={operands[1]} />
        </Flex>
      </Tag>
    );
  }
}

export default Condition;
