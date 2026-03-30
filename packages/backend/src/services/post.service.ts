import { Injectable, ForbiddenException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Post } from '../entities/post.entity';

@Injectable()
export class PostService {
  constructor(
    @InjectRepository(Post)
    private postRepository: Repository<Post>,
  ) {}

  /**
   * 投稿を削除（管理者のみ）
   * 一般ユーザーは削除不可
   */
  async deletePost(postId: string, userId: string, isAdmin: boolean): Promise<void> {
    const post = await this.postRepository.findOne({ where: { id: postId } });

    if (!post) {
      throw new Error('Post not found');
    }

    // 一般ユーザーは削除不可
    if (!isAdmin) {
      throw new ForbiddenException(
        '一度公開された投稿は削除できません。このポリシーにより、ユーザーは投稿に責任を持つことが求められます。'
      );
    }

    // 管理者のみ削除可能（法的理由のみ）
    // 削除ログを記録
    await this.logAdminDeletion(postId, userId, 'Admin deletion');

    await this.postRepository.softDelete(postId);
  }

  private async logAdminDeletion(postId: string, adminId: string, reason: string): Promise<void> {
    // TODO: 削除ログをAudit Logに記録
    console.log(`Admin ${adminId} deleted post ${postId}: ${reason}`);
  }
}
