import traceback
import re
import json
import datetime
from zoneinfo import ZoneInfo
from pymongo import MongoClient, ASCENDING


class Enrichment:
    """
    This class implements the enrichment functionality from BigPanda's enrichment engine.

    Args:

    mongo_url (str): The URL of the MongoDB instance to use for enrichment configuration.

    debug (bool): If True, add debug messages to the event.

    broken_regex (bool): If True, fix broken regexes by changing * to .*, escaping parentheses, etc.

    prepend_path (str): A path to prepend to all enrichment paths. This is useful if you want to
      use enrichment rules that were developed for a different event format.

    tz (str): The time zone to use for timestamps. This should be a valid time zone name from the
      IANA Time Zone Database (https://www.iana.org/time-zones). The default is UTC.
    
    db_name (str): The name of the MongoDB database to use for enrichment configuration.

    enrich_metadata_collection_name (str): The name of the MongoDB collection that contains the list of
        enrichment rulesets.
    
    enrich_collection_prefix (str): The prefix to use for the names of the MongoDB collections that contain
        the enrichment rules.

    maintenances_collection_name (str): The name of the MongoDB collection that contains the list of
        maintenance windows.

    correlations_collection_name (str): The name of the MongoDB collection that contains the list of
        correlation rules.
    """

    def __init__(
        self,
        mongo_url,
        debug=False,
        broken_regex=False,
        prepend_path="",
        tz="UTC",
        db_name="pdaltagent",
        enrich_metadata_collection_name="_enrich_metadata",
        enrich_collection_prefix="enrich_",
        maintenances_collection_name="maint",
        correlations_collection_name="correlation",
    ):
        self.mongo_url = mongo_url
        self.debug = debug
        self.broken_regex = broken_regex
        self.prepend_path = prepend_path
        self.time_zone = ZoneInfo(tz)
        self.db_name = db_name
        self.enrich_metadata_collection_name = enrich_metadata_collection_name
        self.enrich_collection_prefix = enrich_collection_prefix
        self.maintenances_collection_name = maintenances_collection_name
        self.correlations_collection_name = correlations_collection_name

        self.maintenances = []
        self.enrichment_metadata = []
        self.enrichments = []
        self.correlations = []

        if self.mongo_url:
            self.client = MongoClient(self.mongo_url)
            self.db = self.client[self.db_name]
            self.load_from_mongo()

    def load_from_mongo(self):
        """
        Load enrichment configuration from MongoDB. Assign to instance variables.

        Returns:
        None
        """

        if self.debug:
            print(
                f"Loading enrichment configuration from MongoDB..."
            )

        # Load maintenance windows
        self.maintenances = list(
            self.db[self.maintenances_collection_name].find({}, {"_id": 0})
        )

        active_enrichments = list(self.db[self.enrich_metadata_collection_name].find({"active": True}, {"_id": 0}))
        active_enrichments_sorted = sorted(active_enrichments, key=lambda x: x.get("order", float("inf")))
        self.enrichment_metadata = active_enrichments_sorted

        # Load enrichment rules
        self.enrichments = []
        for enrichment_metadata in self.enrichment_metadata:
            if not ("active" in enrichment_metadata and enrichment_metadata["active"]):
                continue
            enrichment_name = enrichment_metadata["name"]
            enrichment_type = enrichment_metadata["type"]
            collection_name = self.enrich_collection_prefix + enrichment_name
            enrichment_rules = list(
                self.db[collection_name].find({"active": True}, {"_id": 0})
            )
            enrichment_rules_sorted = sorted(enrichment_rules, key=lambda x: x.get("order", float("inf")))
            self.enrichments.append(
                {
                    "name": enrichment_name,
                    "type": enrichment_type,
                    "rules": enrichment_rules_sorted,
                }
            )

        active_correlations = list(self.db[self.correlations_collection_name].find({"active": True}, {"_id": 0}))
        active_correlations_sorted = sorted(active_correlations, key=lambda x: x.get("order", float("inf")))
        self.correlations = active_correlations_sorted

        if self.debug:
            print(f"Loaded {len(self.maintenances)} maintenance windows")
            print(f"Loaded {len(self.enrichment_metadata)} enrichment metadata records")
            print(f"Loaded {len(self.enrichments)} enrichment rule sets")
            print(f"Loaded {len(self.correlations)} correlation rules")
            enrichment_tag_order_str = "Enrichment tag order: " + \
                ", ".join(
                    [f"{x['name']} ({x.get('order', 'inf')})" for x in self.enrichment_metadata]
                )
            print(enrichment_tag_order_str)

    def add_message_to_event(self, event, message, is_debug=False):
        if is_debug and not self.debug:
            return
        if self.get_value_at_path(event, "payload.custom_details.messages") is None:
            self.set_value_at_path(event, "payload.custom_details.messages", [])
        messages = self.get_value_at_path(event, "payload.custom_details.messages")
        messages.append(message)

    def make_path(self, prepend_path, path):
        """
        Make a path by prepending a string to another string.
        if prepend_path is None, it is treated as an empty string.
        if path starts with a dot, it is removed, and the prepend_path is ignored,
        so that path is treated as an absolute path.
        """
        if prepend_path is None:
            prepend_path = ''
        if path.startswith("."):
            return path[1:]
        return prepend_path + path

    def get_value_at_path(self, data, path):
        """
        Get the value at a specified path in a nested dictionary.

        Args:
        data (dict): The input dictionary.
        path (str): The path to the desired value, separated by dots.

        Returns:
        The value at the specified path or None if the path doesn't exist.
        """
        keys = path.split(".")
        current = data

        try:
            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key)
                elif isinstance(current, list):
                    key = int(key)
                    current = current[key]
                else:
                    return None
            return current
        except:
            return None

    def set_value_at_path(self, data, path, value):
        """
        Set a value at a specified path in a nested dictionary, creating the path if it doesn't exist.
        Modifies data object in place.

        Args:
        data (dict): The input dictionary.
        path (str): The path where the value should be set, separated by dots.
        value: The value to set at the specified path.

        Returns:
        None
        """
        # if path is not a str, or is empty, raise TypeError
        if not path or not isinstance(path, str):
            raise TypeError("Path must be a string")
        keys = path.split(".")
        current = data

        for key in keys[:-1]:
            if isinstance(current, dict):
                if key not in current:
                    current[key] = {}
                current = current[key]
            else:
                raise TypeError("Cannot create path in non-dictionary")

        last_key = keys[-1]
        if isinstance(current, dict):
            current[last_key] = value
        else:
            raise TypeError("Cannot set value in non-dictionary")

    def timestamp_to_human(self, timestamp):
        dt = datetime.datetime.fromtimestamp(timestamp)
        dt_local = dt.astimezone(self.time_zone)
        return dt_local.strftime("%Y-%m-%d %H:%M:%S %Z")

    def remove_falsy_values_from_object(self, obj):
        """
        Remove falsy values from a dictionary or list.

        Args:
        obj (dict or list): The input object.

        Returns:
        The input object with falsy values removed.
        """

        def is_falsy_but_not_false_or_zero(value):
            return type(value) is not bool and type(value) is not int and not value

        if isinstance(obj, dict):
            return {
                key: self.remove_falsy_values_from_object(value)
                for key, value in obj.items()
                if not is_falsy_but_not_false_or_zero(value)
            }
        elif isinstance(obj, list):
            return [
                self.remove_falsy_values_from_object(item)
                for item in obj
                if not is_falsy_but_not_false_or_zero(item)
            ]
        else:
            return obj

    def text_BPQL_to_json(self, text):
        """
        Convert a text BPQL condition to a JSON condition.

        Args:
        text (str): The text BPQL condition.

        Returns:
        The JSON condition (as an object).
        """

        def parse_condition(condition):
            # Adjusted regex to handle regular expressions and other formats
            pattern = r"(\w+)\s*(=|!=|IN|NOT IN)\s*(\[.*?\]|\".*?\"|\/.*?\/)"
            match = re.match(pattern, condition)
            if match:
                field, operator, value = match.groups()
                if value.startswith("["):
                    value = json.loads(value.replace("'", '"'))
                    for i, v in enumerate(value):
                        if isinstance(v, str) and '*' in v:
                            value[i] = {"type": "regex", "value": v.strip('"')}
                elif value.startswith("/") and value.endswith("/"):
                    value = {"type": "regex", "value": value.strip("/")}
                elif '*' in value:
                    value = {"type": "regex", "value": value.strip('"')}
                else:
                    value = value.strip('"')
                return {operator: [field, value]}
            else:
                raise ValueError(f"Invalid condition: {condition}")

        def split_conditions(expression):
            # Split conditions while respecting nested structures
            parts = []
            depth = 0
            start = 0
            for i, char in enumerate(expression):
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                elif depth == 0 and expression[i : i + 3] in ["AND", "OR"]:
                    parts.append(expression[start:i].strip())
                    parts.append(expression[i : i + 3].strip())
                    start = i + 4
            parts.append(expression[start:].strip())
            return parts

        def parse_expression(expression):
            conditions = split_conditions(expression)
            if len(conditions) == 1:
                return parse_condition(conditions[0])

            result = {}
            for i in range(0, len(conditions), 2):
                if conditions[i].startswith("(") and conditions[i].endswith(")"):
                    parsed = parse_expression(conditions[i][1:-1])
                else:
                    parsed = parse_condition(conditions[i])
                operator = conditions[i + 1] if i + 1 < len(conditions) else "AND"
                if operator in result:
                    result[operator].append(parsed)
                else:
                    result[operator] = [parsed]
            return result

        # Remove outer parentheses if present
        if text.startswith("(") and text.endswith(")"):
            text = text[1:-1]

        return parse_expression(text)

    def fix_regex(self, regex):
        """
        Fix broken regexes by changing * to .*, escaping parentheses, etc.
        """
        debug = self.debug
        new_value = regex
        if re.search(r"(?<!\.)\*", new_value):
            # change * to .*
            new_value = re.sub(r"(?<!\.)\*", r".*", new_value)
        if re.search(r"(?<!\\)[()]", new_value):
            # escape parentheses
            new_value = re.sub(r"(?<!\\)([()])", r"\\\1", new_value)
        # if debug and new_value != regex:
        #   print(f"fix_regex: Changing {regex} to {new_value}")
        return new_value

    def equals_operator(self, operand1, operand2, broken_regex=None):
        """
        Evaluate a BPQL = operator.
        """
        # operator 2 can either be a string or a dict with keys "type" and "value"
        # known types are "regex". Regexes follow Elasticsearch Regular Expression Syntax.
        # = operator on string is case-insensitive when operand 2 is a string, and
        # case-sensitive when operand 2 is a regex.
        if broken_regex is None:
            broken_regex = self.broken_regex
        if operand1 is None:
            return False
        left = str(operand1)
        right = operand2
        if isinstance(right, str):
            return left.lower() == right.lower()
        elif isinstance(right, dict):
            if right["type"] == "regex":
                regex = right["value"]
                if broken_regex:
                    regex = self.fix_regex(regex)
                try:
                    return re.search(regex, left, re.IGNORECASE) is not None
                except re.error:
                    print(f"Invalid regex {regex}")
                    return False
            elif right["type"] == "formal-regex":
                regex = right["value"]
                # if broken_regex:
                #     regex = self.fix_regex(regex)
                try:
                    return re.search(regex, left) is not None
                except re.error:
                    if broken_regex:
                        print(f"Invalid regex {regex}, trying to fix it... ", end='', flush=True)
                        try:
                            regex = self.fix_regex(regex)
                            print(f"fixed to {regex}")
                            return re.search(regex, left) is not None
                        except re.error:
                            print(f"still invalid regex {regex}")
                            return False
                    return False
            else:
                raise ValueError(f"Unsupported type {right['type']}")
        else:
            raise ValueError(f"Unsupported type {type(right)}")

    def in_operator(self, operand1, operand2, broken_regex=None):
        """
        Evaluate a BPQL IN operator.
        """
        # operand 1 is the same as equals_operator, operand 2 is a list that can be
        # mixed strings and dicts as in equals_operator
        if broken_regex is None:
            broken_regex = self.broken_regex
        if isinstance(operand2, list):
            return any(
                self.equals_operator(operand1, x, broken_regex) for x in operand2
            )
        else:
            raise ValueError(f"Unsupported type {type(operand2)}")

    def evaluate_condition(
        self, entity, condition, broken_regex=None, prepend_path=None
    ):
        """
        Evaluate a BPQL condition.
        """
        if broken_regex is None:
            broken_regex = self.broken_regex
        if prepend_path is None:
            prepend_path = self.prepend_path
        # I think BP treats null condition as always true
        if condition is None:
            return True
        for operator, operands in condition.items():
            path = None
            if operator.lower() in ["=", "!=", "in", "not in"]:
                path = self.make_path(prepend_path, operands[0])
            if operator == "=":
                operand1 = self.get_value_at_path(entity, path)
                if operand1 is None:
                    return False
                operand2 = operands[1]
                return self.equals_operator(operand1, operand2, broken_regex)
            if operator == "!=":
                operand1 = self.get_value_at_path(entity, path)
                if operand1 is None:
                    return True
                operand2 = operands[1]
                return not self.equals_operator(operand1, operand2, broken_regex)
            elif operator == "IN":
                operand1 = self.get_value_at_path(entity, path)
                if operand1 is None:
                    return False
                operand2 = operands[1]
                return self.in_operator(operand1, operand2, broken_regex)
            elif operator == "NOT IN":
                operand1 = self.get_value_at_path(entity, path)
                if operand1 is None:
                    return True
                operand2 = operands[1]
                return not self.in_operator(operand1, operand2, broken_regex)
            elif operator == "OR":
                if not any(
                    self.evaluate_condition(
                        entity, sub_condition, broken_regex, prepend_path
                    )
                    for sub_condition in operands
                ):
                    return False
            elif operator == "AND":
                if not all(
                    self.evaluate_condition(
                        entity, sub_condition, broken_regex, prepend_path
                    )
                    for sub_condition in operands
                ):
                    return False
            else:
                raise ValueError(f"Unsupported operator {operator} in condition {json.dumps(condition)}")
        return True

    def apply_regex_and_fill_template(self, input_string, regex, template):
        """
        Apply a regex to a string and fill a template with the results.
        """
        _input_string = input_string
        if input_string is None:
            return None
        if type(input_string) is dict:
            _input_string = json.dumps(input_string)
        elif type(input_string) is list:
            _input_string = '\n'.join(input_string)
        elif type(input_string) is not str:
            _input_string = str(input_string)
        if type(regex) is not str:
            raise ValueError(f"apply_regex_and_fill_template: regex must be a string, not {type(regex)} (got {regex})")
        if type(template) is not str:
            raise ValueError(f"apply_regex_and_fill_template: template must be a string, not {type(template)} (got {template})")

        match = re.search(regex, _input_string)
        if match:
            temp = template
            for i in range(1, len(match.groups()) + 1):
                temp = temp.replace(f"${i}", match.group(i))
            # if there are still any $1 $2 etc in the value then we failed and should return None
            if re.search(r"\$\d+", temp):
                return None
            return temp
        return None

    def do_mapping(self, entity, mapping_obj, prepend_path=None, debug_enrichment=False):
        """
        Perform a BigPanda enrichment of type "mapping"

        Modifications to the entity are made in place.
        """
        if prepend_path is None:
            prepend_path = self.prepend_path
        if (
            not prepend_path
            and "payload" in entity
            and "custom_details" in entity["payload"]
        ):
            prepend_path = "payload.custom_details."

        mapping = mapping_obj["config"]
        rule_id = mapping_obj.get("id", "no mapping id")

        collection_name = "mapping_" + mapping["name"]
        try:
            self.db.list_collections(filter={"name": collection_name}).next()
        except StopIteration:
            self.add_message_to_event(
                entity,
                f"do_mapping: collection {collection_name} not found",
                is_debug=True,
            )
            return
        collection = self.db[collection_name]
        fields = mapping["fields"]
        query_fields = [f for f in fields if f["type"] == "query_tag"]
        result_fields = [f for f in fields if f["type"] == "result_tag"]
        query = {}
        for f in query_fields:
            query_key = f["tag_name"]
            query_value = self.get_value_at_path(entity, prepend_path + f["tag_name"])
            if query_value is None:
                not_found_message = f"do_mapping: query field {f['tag_name']} not found"
                if f["optional"] == False:
                    not_found_message += " (required)"
                    return
                self.add_message_to_event(entity, not_found_message, is_debug=True)
            else:
                query[query_key] = query_value
        if len(query) == 0:
            self.add_message_to_event(entity, f"do_mapping: no query fields found")
            return
        query_message = f"do_mapping: query {json.dumps(query)}"
        query_result = collection.find_one(query, {"_id": 0})
        if query_result is None:
            query_message += " returned no results"
            self.add_message_to_event(entity, query_message, is_debug=True)
            return
        query_message += f" returned {json.dumps(query_result)}"
        self.add_message_to_event(
            entity,
            query_message,
            is_debug=False,
        )
        for f in result_fields:
            if (
                f["override_existing"] == False
                and self.get_value_at_path(entity, prepend_path + f["tag_name"])
                is not None
            ):
                continue
            if query_result.get(f["tag_name"]):
                self.set_value_at_path(
                    entity,
                    self.make_path(prepend_path, f["tag_name"]),
                    query_result.get(f["tag_name"]),
                )
                if debug_enrichment:
                    self.set_value_at_path(
                        entity,
                        prepend_path + f"enrichments.{f['tag_name'].lstrip('.')}",
                        {
                            'value': query_result.get(f["tag_name"]),
                            'rule_type': 'mapping',
                            'rule_id': rule_id,
                        }
                    )

    def custom_interpolate(self, template, values):
        # Regular expression to find ${key} patterns
        pattern = re.compile(r'\${(\w+)}')

        # Function to replace each match
        def replace(match):
            key = match.group(1)
            return values[key]

        # Replace all matches in the template
        return pattern.sub(replace, template)

    def do_composition(self, entity, composition_obj, prepend_path=None, debug_enrichment=False):
        """
        Perform a BigPanda enrichment of type "composition"

        Modifications to the entity are made in place.
        """
        if prepend_path is None:
            prepend_path = self.prepend_path

        did_something = False

        composition = composition_obj["config"]
        rule_id = composition_obj.get("id", "no composition id")

        targets = composition["destinations"] if "destinations" in composition else [composition]
        for target in targets:
            destination = self.make_path(prepend_path, target["destination"])
            value = target["value"]

            if isinstance(value, str) and re.search(r"\${(\w+)}", value):
                # Value contains a template, so we need to interpolate it
                interpolation_data = entity
                if prepend_path:
                    interpolation_data = self.get_value_at_path(entity, prepend_path.rstrip("."))
                if interpolation_data is None:
                    self.add_message_to_event(
                        entity, f"do_composition: no interpolation data found", is_debug=True
                    )
                    continue
                else:
                    try:
                        value = self.custom_interpolate(value, interpolation_data)
                    except KeyError as e:
                        # if the interpolation data is missing a key that is in the template, we can't interpolate
                        self.add_message_to_event(
                            entity, f"do_composition: interpolation failed: {e}", is_debug=True
                        )
                        continue

            self.add_message_to_event(
                entity, f"do_composition: {value} => {destination}", is_debug=bool(value)
            )

            self.set_value_at_path(entity, destination, value)
            if debug_enrichment:
                self.set_value_at_path(
                    entity,
                    f"{prepend_path}enrichments.{target['destination'].lstrip('.')}",
                    {
                        'value': value,
                        'rule_type': 'composition',
                        'rule_id': rule_id,
                    }
                )

        return True

    def do_extraction(self, entity, extraction_obj, prepend_path=None, debug_enrichment=False):
        """
        Perform a BigPanda enrichment of type "extraction"

        Modifications to the entity are made in place.
        """
        if prepend_path is None:
            prepend_path = self.prepend_path
        
        extraction = extraction_obj["config"]
        rule_id = extraction_obj.get("id", "no extraction id")

        source = self.make_path(prepend_path, extraction["source"])
        destination = self.make_path(prepend_path, extraction["destination"])
        regex = extraction["regex"]
        template = extraction["template"]

        message_str = f"do_extraction: {source} {regex} {template} => {destination}"
        input_string = self.get_value_at_path(entity, source)
        if not input_string:
            self.add_message_to_event(
                entity, message_str + f" source {source} not found", is_debug=True
            )
            return
        output_string = self.apply_regex_and_fill_template(
            input_string, regex, template
        )
        if not output_string:
            self.add_message_to_event(
                entity, message_str + f" regex {regex} did not match", is_debug=True
            )
            return

        self.add_message_to_event(
            entity, message_str + f" {input_string} => {output_string}"
        )
        self.set_value_at_path(entity, destination, output_string)
        if debug_enrichment:
            self.set_value_at_path(
                entity,
                f"{prepend_path}enrichments.{extraction['destination'].lstrip('.')}",
                {
                    'value': output_string,
                    'rule_type': 'extraction',
                    'rule_id': rule_id,
                }
            )
        return True

    def do_enrichment(self, entity, enrichment, prepend_path=None, debug_enrichment=False):
        """
        Perform a BigPanda enrichment of any type

        Args:
        entity (dict): The event entity to enrich.
        enrichment (dict): The enrichment rule to apply.
        prepend_path (str): A path to prepend to all enrichment paths. This is useful if you want to
          use enrichment rules that were developed for a different event format.

        Modifications to the entity are made in place.
        """
        if prepend_path is None:
            prepend_path = self.prepend_path
        # TODO: match selected source system on events
        selected_source_system = None
        try:
            # not all enrichments have a selected_source_system, evidently
            selected_source_system = enrichment["config"]["selected_source_system"]
        except:
            pass

        if selected_source_system:
            source_system = self.get_value_at_path(entity, self.make_path(prepend_path, "source_system"))
            if source_system:
                # source system can be a broken regex
                selected_source_system = self.fix_regex(selected_source_system)
                if not re.search(selected_source_system, source_system, re.IGNORECASE):
                    self.add_message_to_event(
                        entity,
                        f"do_enrichment: enrichment {enrichment['id']} not applied because source system {selected_source_system} does not match {source_system}",
                    )
                    return

        enrichment_type = enrichment["type"]
        # known enrichment types are 'mapping', 'composition' and 'extraction'
        try:
            if enrichment_type == "mapping":
                if enrichment["when"] is not None:
                    if not self.evaluate_condition(
                        entity,
                        enrichment["when"],
                        broken_regex=True,
                        prepend_path=prepend_path,
                    ):
                        self.add_message_to_event(
                            entity,
                            f"do_enrichment: enrichment {enrichment['id']} not applied because when condition is false",
                        )
                        return
                return self.do_mapping(entity, enrichment, prepend_path=prepend_path, debug_enrichment=debug_enrichment)
            elif enrichment_type == "composition":
                return self.do_composition(
                    entity, enrichment, prepend_path=prepend_path, debug_enrichment=debug_enrichment
                )
            elif enrichment_type == "extraction":
                return self.do_extraction(
                    entity, enrichment, prepend_path=prepend_path, debug_enrichment=debug_enrichment
                )
            else:
                raise ValueError(f"Unsupported enrichment type {enrichment_type}")
        except Exception as e:
            print(f"do_enrichment: error applying enrichment {enrichment}: {e}")
            traceback.print_exc()
            return False

    def is_active_now(self, maint):
        """
        Check if a maintenance window is active now.

        Args:
        maint (dict): The maintenance window to check.

        Returns:
        True if the maintenance window is active now, False otherwise.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        start = datetime.datetime.fromtimestamp(maint["start"], datetime.timezone.utc)
        end = datetime.datetime.fromtimestamp(maint["end"], datetime.timezone.utc)
        frequency = maint["frequency"].lower()
        frequency_data = maint["frequency_data"]
        if frequency == "once":
            return start <= now <= end
        elif frequency == "daily":
            # frequency_data has "duration" in seconds; start at start and advance by one day until we pass now,
            # then go back one and check if now is less than duration seconds after that
            current = start
            while current <= now:
                current += datetime.timedelta(days=1)
            current -= datetime.timedelta(days=1)
            # current is now the latest start that's in the past; check if it's within the duration
            return (
                current
                <= now
                <= current + datetime.timedelta(seconds=frequency_data["duration"])
            )
        elif frequency == "weekly":
            current = start
            while current <= now:
                current += datetime.timedelta(weeks=1)
            current -= datetime.timedelta(weeks=1)
            return (
                current
                <= now
                <= current + datetime.timedelta(seconds=frequency_data["duration"])
            )

    def is_in_maint(self, event):
        """
        Check if an event is in maintenance.

        Args:
        event (dict): The event to check.

        Returns:
        A tuple (is_in_maint, maints_applied) where is_in_maint is True if the event is in maintenance,
            False otherwise, and maints_applied is a list of the maintenance windows that apply.
        """
        maints_now = [maint for maint in self.maintenances if self.is_active_now(maint)]
        maints_applied = [maint for maint in maints_now if self.evaluate_condition(event, maint["condition"])]
        is_in_maint = len(maints_applied) > 0
        return (is_in_maint, maints_applied)

    def correlation_value(self, event, correlation):
        """
        Perform a BigPanda correlation.

        Args:
        event (dict): The event to correlate.
        correlation (dict): The correlation rule to apply.

        Returns:
        Correlation key and value, or None if the event does not produce a correlation value.
        """
        tags = sorted(correlation["tags"])
        values = [
            self.get_value_at_path(event, f"{self.prepend_path}{tag}") for tag in tags
        ]
        # any None or empty string values mean we can't produce a correlation value
        for v in values:
            if v is None or v == "":
                return None

        k = "+".join(tags)
        v = "+".join(values)
        if not k or not v:
            return None
        return (k, v)

    def do_correlation(self, event, correlation):
        """
        Perform a BigPanda correlation.

        Args:
        event (dict): The event to correlate.
        correlation (dict): The correlation rule to apply.

        Returns:
        Correlation value if the event produces one, None otherwise.
        """
        filter = self.text_BPQL_to_json(correlation["filter"])
        tags = correlation["tags"]
        if self.evaluate_condition(event, filter):
            message_str = f"Matched correlation {correlation['id']}, "
            v = self.correlation_value(event, correlation)
            if v:
                self.add_message_to_event(event, message_str + f"produced value {v}")
                return v
            else:
                self.add_message_to_event(
                    event, message_str + f"no value produced", is_debug=True
                )

    def enrich_event(self, event, debug_enrichment=False):
        """
        Enrich an event.

        Args:
        event (dict): The event to enrich.

        Returns:
        The enriched event.
        """
        for enrichment_set in self.enrichments:
            for enrichment in enrichment_set["rules"]:
                if self.evaluate_condition(event, enrichment["when"]):
                    message_str = (
                        f"Matched rule {enrichment_set['name']}: {enrichment['id']}"
                    )
                    if self.do_enrichment(event, enrichment, debug_enrichment=debug_enrichment):
                        if enrichment_set["type"] == "match_first":
                            self.add_message_to_event(
                                event,
                                message_str + f" - applied + stopping (match_first)",
                            )
                            break
                        else:
                            self.add_message_to_event(
                                event, message_str + f" - applied"
                            )
                    else:
                        message_str += f" - not applied"
                        self.add_message_to_event(event, message_str, is_debug=True)
        for correlation in self.correlations:
            correlation_value = self.do_correlation(event, correlation)
            if correlation_value:
                self.set_value_at_path(
                    event,
                    f"{self.prepend_path}correlations.{correlation_value[0]}",
                    correlation_value[1],
                )
        return event

    def add_maint(self, maint):
        """
        Add a maintenance window.

        Args:
        maint (dict): The maintenance window to add.

        Returns:
        None
        """
        maint_to_add = json.loads(json.dumps(maint))
        collection = self.db[self.maintenances_collection_name]
        collection.insert_one(maint_to_add)
        self.load_from_mongo()
        return maint_to_add
    
    def delete_maint(self, id):
        """
        Delete a maintenance window.

        Args:
        id (str): The ID of the maintenance window to delete.

        Returns:
        None
        """
        collection = self.db[self.maintenances_collection_name]
        r = collection.find_one({"id": id})
        if r:
            s = collection.delete_one({"id": id})
            print(s)
        else:
            print(f"delete_maint: maintenance window {id} not found")
        self.load_from_mongo()
