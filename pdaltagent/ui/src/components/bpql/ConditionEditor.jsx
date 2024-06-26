import { useRef, useState, useMemo, useEffect, useCallback } from 'react';
import MonacoEditor from 'react-monaco-editor';
import * as monaco from 'monaco-editor';
import { VStack, HStack, Box, Button } from '@chakra-ui/react';
import { stringifyExpression } from '../../util/helpers';
import parser from '../../util/parser';
import Condition from '../Condition';

const ConditionEditor = ({ condition, setCondition, setIsValid, initialMode = "json" }) => {
    const editorRef = useRef(null);
    const [conditionText, setConditionText] = useState(JSON.stringify(condition, null, 2));
    const [language, setLanguage] = useState(initialMode);
    const [errors, setErrors] = useState([]);

    useEffect(() => {
        const lang = editorRef.current.getModel().getLanguageId();
        try {
            if (lang === "json") {
                setConditionText(JSON.stringify(condition, null, 2));
            } else if (lang === "plaintext") {
                setConditionText(stringifyExpression(condition));
            }
        } catch (e) {
            setErrors([e.message]);
        }
        if (editorRef.current) {
            monaco.editor.setModelLanguage(editorRef.current.getModel(), language);
            editorRef.current.layout();
        }
    }, [condition, language]);

    const valid = useMemo(() => {
        if (language === "json") {
            try {
                const c = JSON.parse(conditionText);
                stringifyExpression(c);
                setErrors([]);
                return true;
            } catch (e) {
                setErrors([e.message]);
                return false;
            }
        } else {
            try {
                parser.parse(conditionText);
                setErrors([]);
                return true;
            } catch (e) {
                setErrors([e.message]);
                return false;
            }
        }
    }, [language, conditionText]);

    useEffect(() => {
      setIsValid(valid);
    }, [valid, setIsValid]);


    const handleEditorChange = useCallback((newValue) => {
        const lang = editorRef.current.getModel().getLanguageId();

        setConditionText(newValue);
        if (lang === "json") {
            try {
                const parsedCondition = JSON.parse(newValue);
                stringifyExpression(parsedCondition); // to check if the parsed condition is valid
                setCondition(parsedCondition);
            } catch (e) {
                // do not set condition if invalid JSON
            }
        } else {
            try {
                const parsedCondition = parser.parse(newValue);
                setCondition(parsedCondition);
            } catch (e) {
                // do not set condition if invalid plaintext
            }
        }
    }, [setCondition]);

    const editorDidMount = (editor) => {
        editorRef.current = editor;
        monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
            validate: true,
            schemas: [],
        });
        editor.getModel().updateOptions({ tabSize: 2 });
    };

    const options = useMemo(() => ({
        selectOnLineNumbers: true,
        automaticLayout: true,
        tabSize: 2,
        wordWrap: language === "plaintext" ? 'on' : 'off',
    }), [language]);

    return (
        <VStack
            borderWidth="1px"
            borderRadius="md"
            p={2}
            spacing={0}
            align="stretch"
            w="100%"
            h="100%"
        >
            <Button
                mb={2}
                colorScheme="blue"
                isDisabled={conditionText && !valid}
                onClick={() => {
                    setLanguage(language === "json" ? "plaintext" : "json");
                }}
            >
                {language === "json" ? "Switch to text" : "Switch to JSON"}
            </Button>
            <HStack spacing={0} w="100%" h="100%">
                <Box
                    w="48vw"
                    h="100%"
                    display="flex"
                    flexDirection="column"
                >
                    <MonacoEditor
                        width="100%"
                        height="100%"
                        language={language}
                        theme="vs-dark"
                        options={options}
                        editorDidMount={editorDidMount}
                        value={conditionText}
                        onChange={handleEditorChange}
                    />
                </Box>
                <Box
                    w="48vw"
                    h="100%"
                >
                    <Box overflow="auto" w="100%" h="100%">
                        {valid && (
                            <Condition condition={condition} />
                        )}
                        {!valid && (
                            errors.map((error, i) => (
                                <Box key={i} color="red">
                                    {error}
                                </Box>
                            ))
                        )}
                    </Box>
                </Box>
            </HStack>
        </VStack>
    );
};

export default ConditionEditor;
