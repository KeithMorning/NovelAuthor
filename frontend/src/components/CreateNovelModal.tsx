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
  Input,
  Select,
  Textarea,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  VStack,
  useToast,
} from '@chakra-ui/react';
import { useCreateNovel, useStyles } from '../hooks/useNovels';
import { CreateNovelRequest } from '../types';
import { CreationProgress } from './CreationProgress';

interface CreateNovelModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CreateNovelModal: React.FC<CreateNovelModalProps> = ({ isOpen, onClose }) => {
  const toast = useToast();
  const createNovel = useCreateNovel();
  const { data: styles, isLoading: stylesLoading } = useStyles();
  const [createdNovelId, setCreatedNovelId] = useState<string | null>(null);

  const [formData, setFormData] = useState<CreateNovelRequest>({
    title: '',
    genre: '科幻',
    theme: '',
    style: '刘慈欣',
    chapters: 5,
  });

  const genres = ['科幻', '武侠', '推理', '奇幻', '现代', '历史', '悬疑'];

  const handleSubmit = async () => {
    if (!formData.title.trim() || !formData.theme.trim()) {
      toast({
        title: '请填写完整信息',
        description: '标题和主题不能为空',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    try {
      const result = await createNovel.mutateAsync(formData);
      // Backend now returns data with novel_id
      if (result.data && result.data.novel_id) {
        setCreatedNovelId(result.data.novel_id);
      } else {
        // Fallback if backend update not picked up yet (or type issue)
        toast({ title: 'Creation started', status: 'success' });
        onClose();
      }
    } catch (error: any) {
      toast({
        title: '创建失败',
        description: error.response?.data?.error || '请稍后重试',
        status: 'error',
        duration: 5000,
      });
    }
  };

  const handleClose = () => {
    setCreatedNovelId(null);
    setFormData({
      title: '',
      genre: '科幻',
      theme: '',
      style: '刘慈欣',
      chapters: 5,
    });
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="xl" closeOnOverlayClick={!createdNovelId}>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>{createdNovelId ? 'Creation in Progress' : '创建新小说'}</ModalHeader>
        {!createdNovelId && <ModalCloseButton />}
        <ModalBody>
          {createdNovelId ? (
            <CreationProgress novelId={createdNovelId} onComplete={handleClose} />
          ) : (
            <VStack gap={4}>
              <FormControl isRequired>
                <FormLabel>小说标题</FormLabel>
                <Input
                  placeholder="输入小说标题"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>类型</FormLabel>
                <Select
                  value={formData.genre}
                  onChange={(e) => setFormData({ ...formData, genre: e.target.value })}
                >
                  {genres.map((genre) => (
                    <option key={genre} value={genre}>
                      {genre}
                    </option>
                  ))}
                </Select>
              </FormControl>

              <FormControl isRequired>
                <FormLabel>主题描述</FormLabel>
                <Textarea
                  placeholder="描述小说的主题和核心内容"
                  value={formData.theme}
                  onChange={(e) => setFormData({ ...formData, theme: e.target.value })}
                  rows={4}
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>写作风格</FormLabel>
                <Select
                  value={formData.style}
                  onChange={(e) => setFormData({ ...formData, style: e.target.value })}
                  isDisabled={stylesLoading}
                >
                  {styles?.map((style) => (
                    <option key={style.name} value={style.name}>
                      {style.name} - {style.description}
                    </option>
                  ))}
                </Select>
              </FormControl>

              <FormControl isRequired>
                <FormLabel>章节数量</FormLabel>
                <NumberInput
                  value={formData.chapters}
                  onChange={(_, value) => setFormData({ ...formData, chapters: value })}
                  min={1}
                  max={100}
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
              </FormControl>
            </VStack>
          )}
        </ModalBody>

        {!createdNovelId && (
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={handleClose}>
              取消
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleSubmit}
              isLoading={createNovel.isPending}
            >
              创建
            </Button>
          </ModalFooter>
        )}
      </ModalContent>
    </Modal>
  );
};
