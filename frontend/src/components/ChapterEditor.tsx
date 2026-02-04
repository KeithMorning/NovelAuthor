import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Button,
  HStack,
  VStack,
  Text,
  Badge,
  useToast,
  IconButton,
  Tooltip,
  Divider,
  useColorModeValue,
  Spinner,
} from '@chakra-ui/react';
import { DownloadIcon, CheckIcon } from '@chakra-ui/icons';
import Editor, { OnMount } from '@monaco-editor/react';

interface ChapterEditorProps {
  novelId: string;
  chapterNumber: number;
  initialContent?: string;
  initialTitle?: string;
  onSave?: (content: string) => Promise<void>;
  readOnly?: boolean;
}

export const ChapterEditor: React.FC<ChapterEditorProps> = ({
  novelId,
  chapterNumber,
  initialContent = '',
  initialTitle = '',
  onSave,
  readOnly = false,
}) => {
  const [content, setContent] = useState(initialContent);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);
  const toast = useToast();
  const editorRef = useRef<any>(null);

  const bg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.100', 'whiteAlpha.100');
  const toolbarBg = useColorModeValue('gray.50', 'whiteAlpha.50');

  // Stats
  const wordCount = content.length;
  const paragraphCount = content.split('\n\n').filter(p => p.trim()).length;

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
  };

  // Auto-save logic
  useEffect(() => {
    if (!hasChanges || readOnly || !onSave) return;
    if (autoSaveTimerRef.current) clearTimeout(autoSaveTimerRef.current);

    autoSaveTimerRef.current = setTimeout(() => {
      handleSave();
    }, 3000);

    return () => {
      if (autoSaveTimerRef.current) clearTimeout(autoSaveTimerRef.current);
    };
  }, [content, hasChanges]);

  const handleSave = async () => {
    if (!onSave || readOnly) return;
    setIsSaving(true);
    try {
      await onSave(content);
      setLastSaved(new Date());
      setHasChanges(false);
    } catch (error: any) {
      toast({
        title: 'Save failed',
        description: error.message,
        status: 'error',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleEditorChange = (value: string | undefined) => {
    const newContent = value || '';
    setContent(newContent);
    if (newContent !== initialContent) setHasChanges(true);
  };

  const handleExport = () => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Chapter_${chapterNumber}.txt`;
    link.click();
    URL.revokeObjectURL(url);
    toast({ title: 'Exported', status: 'success', duration: 2000 });
  };

  return (
    <VStack align="stretch" spacing={0} h="full" bg={bg} borderRadius="xl" boxShadow="sm" overflow="hidden" border="1px solid" borderColor={borderColor}>
      {/* Toolbar */}
      <HStack
        justify="space-between"
        px={4}
        py={3}
        bg={toolbarBg}
        borderBottom="1px solid"
        borderColor={borderColor}
      >
        <HStack spacing={4}>
          <Text fontFamily="heading" fontWeight="600" fontSize="md">
            Chapter {chapterNumber}
          </Text>
          {initialTitle && (
            <Text color="gray.500" fontSize="sm">
              {initialTitle}
            </Text>
          )}
          <Badge colorScheme={readOnly ? 'gray' : 'brand'} variant="subtle">
            {readOnly ? 'READ ONLY' : 'EDITING'}
          </Badge>
        </HStack>

        <HStack spacing={2}>
          <HStack spacing={4} px={3} borderRight="1px solid" borderColor={borderColor}>
            <Text fontSize="xs" color="gray.500" fontWeight="medium">
              WORDS: {wordCount.toLocaleString()}
            </Text>
            <Text fontSize="xs" color="gray.500" fontWeight="medium">
              PARAGRAPHS: {paragraphCount}
            </Text>
          </HStack>

          {!readOnly && (
            <HStack spacing={2}>
              {isSaving ? (
                <HStack spacing={1}>
                  <Spinner size="xs" color="brand.500" />
                  <Text fontSize="xs" color="brand.500">Saving...</Text>
                </HStack>
              ) : hasChanges ? (
                <Text fontSize="xs" color="orange.500">Unsaved changes</Text>
              ) : lastSaved ? (
                <Text fontSize="xs" color="gray.400">Saved {lastSaved.toLocaleTimeString()}</Text>
              ) : null}

              <Button
                size="sm"
                variant={hasChanges ? 'solid' : 'ghost'}
                colorScheme={hasChanges ? 'brand' : 'gray'}
                onClick={handleSave}
                isLoading={isSaving}
                leftIcon={<CheckIcon />}
              >
                Save
              </Button>
            </HStack>
          )}

          <Tooltip label="Export to TXT">
            <IconButton
              aria-label="Export"
              icon={<DownloadIcon />}
              size="sm"
              variant="ghost"
              onClick={handleExport}
            />
          </Tooltip>
        </HStack>
      </HStack>

      {/* Editor Area */}
      <Box flex={1} position="relative">
        <Editor
          height="100%"
          defaultLanguage="markdown"
          value={content}
          onChange={handleEditorChange}
          onMount={handleEditorDidMount}
          theme={useColorModeValue('light', 'vs-dark')}
          options={{
            readOnly,
            fontFamily: "'Merriweather', 'Georgia', serif",
            fontSize: 16,
            lineHeight: 1.8,
            wordWrap: 'on',
            minimap: { enabled: false },
            padding: { top: 32, bottom: 32 },
            scrollBeyondLastLine: false,
            smoothScrolling: true,
            cursorBlinking: 'smooth',
            cursorSmoothCaretAnimation: 'on',
            renderLineHighlight: 'none',
            hideCursorInOverviewRuler: true,
            overviewRulerBorder: false,
            scrollbar: {
              verticalScrollbarSize: 8,
              horizontalScrollbarSize: 8,
              useShadows: false,
            },
          }}
          loading={<Spinner size="xl" thickness="3px" color="brand.500" />}
        />
      </Box>
    </VStack>
  );
};
