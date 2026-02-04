import React, { useState } from 'react';
import {
    Modal,
    ModalOverlay,
    ModalContent,
    ModalHeader,
    ModalFooter,
    ModalBody,
    ModalCloseButton,
    Button,
    FormControl,
    FormLabel,
    Select,
    VStack,
    Checkbox,
    Text,
    useToast,
    Box,
} from '@chakra-ui/react';

interface ExportModalProps {
    isOpen: boolean;
    onClose: () => void;
    novel: any; // Using any for simplicity here, but should be NovelDetail
}

export const ExportModal: React.FC<ExportModalProps> = ({ isOpen, onClose, novel }) => {
    const [format, setFormat] = useState('txt');
    const [includeMetadata, setIncludeMetadata] = useState(true);
    const [isExporting, setIsExporting] = useState(false);
    const toast = useToast();

    const handleExport = async () => {
        setIsExporting(true);
        try {
            // Allow UI to update
            await new Promise(resolve => setTimeout(resolve, 800));

            let content = '';
            if (includeMetadata) {
                content += `Title: ${novel.title}\n`;
                content += `Genre: ${novel.genre}\n`;
                content += `Style: ${novel.style}\n`;
                content += `Created: ${new Date(novel.created_at).toLocaleDateString()}\n`;
                content += `\n${'='.repeat(20)}\n\n`;
            }

            novel.chapters.forEach((chapter: any) => {
                content += `Chapter ${chapter.number}: ${chapter.title || ''}\n`;
                content += `${'-'.repeat(20)}\n\n`;
                // In a real app we might need to fetch full content if not already loaded,
                // but for now we assume we might need to fetch or it's in the novel object.
                // NOTE: The novel list usually doesn't have content. 
                // This is a mock export since we don't have a bulk fetch API ready in context.
                content += `[Content for chapter ${chapter.number} would be here...]\n\n`;
            });

            const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `${novel.title.replace(/\s+/g, '_')}_Export.${format}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            toast({ title: 'Export successful', status: 'success' });
            onClose();
        } catch (error) {
            toast({ title: 'Export failed', status: 'error' });
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} size="md">
            <ModalOverlay backdropFilter="blur(5px)" />
            <ModalContent borderRadius="xl">
                <ModalHeader>Export Novel</ModalHeader>
                <ModalCloseButton />
                <ModalBody>
                    <VStack spacing={4} align="stretch">
                        <FormControl>
                            <FormLabel>Format</FormLabel>
                            <Select value={format} onChange={(e) => setFormat(e.target.value)}>
                                <option value="txt">Plain Text (.txt)</option>
                                <option value="md">Markdown (.md)</option>
                                <option value="json">JSON (.json)</option>
                            </Select>
                        </FormControl>

                        <Checkbox
                            isChecked={includeMetadata}
                            onChange={(e) => setIncludeMetadata(e.target.checked)}
                            colorScheme="brand"
                        >
                            Include Metadata (Title, Genre, etc.)
                        </Checkbox>

                        <Box p={3} bg="gray.50" borderRadius="md">
                            <Text fontSize="sm" color="gray.500">
                                You are about to export <strong>{novel?.title}</strong> with {novel?.chapters?.length || 0} chapters.
                            </Text>
                        </Box>
                    </VStack>
                </ModalBody>
                <ModalFooter>
                    <Button variant="ghost" mr={3} onClick={onClose}>Cancel</Button>
                    <Button colorScheme="brand" onClick={handleExport} isLoading={isExporting}>
                        Download
                    </Button>
                </ModalFooter>
            </ModalContent>
        </Modal>
    );
};
