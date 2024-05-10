import { useEffect, useState } from 'react';
import {
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Flex,
  FormControl,
  FormLabel,
  Stack,
} from '@chakra-ui/react';

function DurationInput({
  onChange,
}) {
  const [days, setDays] = useState(0);
  const [hours, setHours] = useState(0);
  const [minutes, setMinutes] = useState(0);

  useEffect(() => {
    onChange((days * 24 * 60 + hours * 60 + minutes) * 60);
  }, [days, hours, minutes, onChange]);

  return (
    <Flex align="center">
      <Stack direction="row" spacing={4}>
        <FormControl>
          <FormLabel htmlFor="days">Days</FormLabel>
          <NumberInput id="days" min={0} value={days} onChange={(valueString) => setDays(parseInt(valueString))}>
            <NumberInputField />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
        </FormControl>

        <FormControl>
          <FormLabel htmlFor="hours">Hours</FormLabel>
          <NumberInput id="hours" min={0} max={23} value={hours} onChange={(valueString) => setHours(parseInt(valueString))}>
            <NumberInputField />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
        </FormControl>

        <FormControl>
          <FormLabel htmlFor="minutes">Minutes</FormLabel>
          <NumberInput id="minutes" min={0} max={59} value={minutes} onChange={(valueString) => setMinutes(parseInt(valueString))}>
            <NumberInputField />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
        </FormControl>
      </Stack>
    </Flex>
  );
}

export default DurationInput;
