import peggy from 'peggy';

const grammar = String.raw`Expression
= LogicalOR

LogicalOR
= head:LogicalAND tail:(_ "OR" _ LogicalAND)* {
    if (tail.length === 0) {
      return head;  // Return just the head if no tail
    }
    return { OR: [head, ...tail.map(element => element[3])] };
  }

LogicalAND
= head:Primary tail:(_ "AND" _ Primary)* {
    if (tail.length === 0) {
      return head;  // Return just the head if there is only one condition
    }
    return { AND: [head, ...tail.map(element => element[3])] };
  }

Primary
= "(" _ expr:Expression _ ")" { return expr; }
/ Condition

Condition
= left:Identifier _ operator:("!=" / "=") _ right:StringOrRegex {
    return { [operator]: [left, right] };
  }
/ left:Identifier _ operator:("IN" / "NOT IN") _ right:List {
    return { [operator]: [left, right] };
  }

Identifier
= id:$[a-zA-Z0-9_\.]* { return id; }

StringOrRegex
= String
/ FormalRegex

FormalRegex
= "/" chars:((RegexChar / SpecialRegexChar)*) "/" {
    return { type: "formal-regex", value: chars.join("") };
  }

RegexChar
= [^\/\\] // Matches any character except forward slashes and backslashes

SpecialRegexChar
= "\\/" { return "/"; } // Explicitly handle escaped forward slashes
/ "\\(" { return "("; }
/ "\\)" { return ")"; }
/ "\\*" { return "*"; }
/ [.*+?^\${}()|[\]\\] // Include all typical regex special characters

String
= "\"" chars:((Char / SpecialChar)*) "\"" {
    const string = chars.join("");
    if (string.includes("*")) {
      return { type: "regex", value: string };
    } else {
      return string;
    }
  }

Char
= NormalChar / EscapedChar

EscapedChar
= "\\\"" { return "\""; }
/ "\\\\" { return "\\"; }

NormalChar
= [^"\\*]  // Exclude *, ", and \ from normal chars to easily classify InformalRegex

SpecialChar
= "*" { return "*"; }
/ "." { return "."; }
/ "(" { return "("; }
/ ")" { return ")"; }

List
= "[" _ items:ListItems? _ "]" { return items || []; }

ListItems
= head:StringOrRegex tail:(_ "," _ StringOrRegex)* {
    return [head, ...tail.map(element => element[3])];
  }

_ "whitespace"
= [ \t\n\r]*
`;

const parser = peggy.generate(grammar);

export default parser;
