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
  value = 0,
  onChange,
  size = "sm",
}) {
  const [days, setDays] = useState(Math.floor(value / (24 * 60 * 60)));
  const [hours, setHours] = useState(Math.floor((value % (24 * 60 * 60)) / (60 * 60)));
  const [minutes, setMinutes] = useState(Math.floor((value % (60 * 60)) / 60));

  useEffect(() => {
    setDays(Math.floor(value / (24 * 60 * 60)));
    setHours(Math.floor((value % (24 * 60 * 60)) / (60 * 60)));
    setMinutes(Math.floor((value % (60 * 60)) / 60));
  }, [value]);

  useEffect(() => {
    onChange((days * 24 * 60 + hours * 60 + minutes) * 60);
  }, [days, hours, minutes, onChange]);

  return (
    <Flex align="center">
      <Stack direction="row" spacing={4}>
        <FormControl>
          <FormLabel size={size} htmlFor="days">Days</FormLabel>
          <NumberInput size={size} id="days" min={0} value={days} onChange={(valueString) => setDays(parseInt(valueString) || 0)}>
            <NumberInputField />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
        </FormControl>

        <FormControl>
          <FormLabel size={size} htmlFor="hours">Hours</FormLabel>
          <NumberInput size={size} id="hours" min={0} max={23} value={hours} onChange={(valueString) => setHours(parseInt(valueString) || 0)}>
            <NumberInputField />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
        </FormControl>

        <FormControl>
          <FormLabel size={size} htmlFor="minutes">Minutes</FormLabel>
          <NumberInput size={size} id="minutes" min={0} max={59} value={minutes} onChange={(valueString) => setMinutes(parseInt(valueString) || 0)}>
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
