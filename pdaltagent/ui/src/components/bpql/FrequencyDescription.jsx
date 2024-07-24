import {
  // Box,
  Text,
} from "@chakra-ui/react";

import { describeEvent } from "../../util/helpers";

const FrequencyDescription = ({
  start,
  end,
  frequency,
  duration,
}) => (
  <Text fontSize="xs" fontStyle="italic" textColor="darkgray">{describeEvent(start, end, duration, frequency)}</Text>
);

export default FrequencyDescription;