// 공통 임베드 포맷 함수 추가 - 모든 임베드에 적용할 표준 양식
function createBaseEmbed(color, title, description) {
    return new EmbedBuilder()
      .setColor(color)
      .setTitle(title)
      .setDescription(description)
      .setAuthor({ name: 'Aimbot.ad', iconURL: 'https://imgur.com/Sd8qK9c.gif' }); 
      // 모든 임베드에 setAuthor 통일
  }
  
  /**
   * 티켓 임베드 생성
   * @param {Interaction} interaction 상호작용 객체
   */
  async createTicketEmbed(interaction) {
    try {
      await interaction.deferReply({ ephemeral: true });
      
      const channel = interaction.options.getChannel('채널');
      
      // 채널 권한 확인
      if (!channel.permissionsFor(interaction.guild.members.me).has(PermissionsBitField.Flags.SendMessages)) {
        const errorEmbed = createBaseEmbed('#ED4245', '❌ 권한 오류', `${channel} 채널에 메시지를 보낼 권한이 없습니다.`)
          .addFields({ name: '해결 방법', value: '봇에게 필요한 권한을 부여해주세요.', inline: false })
          .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
          .setTimestamp();
            
        return await interaction.editReply({ embeds: [errorEmbed], ephemeral: true });
      }
      
      // 서버 설정 가져오기 또는 생성
      let settings = this.guildSettings.get(interaction.guild.id) || {};
      settings.ticketChannel = channel.id;
      
      // 설정 저장
      this.updateGuildSettings(interaction.guild.id, settings);
      
      // 티켓 임베드 생성
      const ticketEmbed = createBaseEmbed('#5865F2', '🎫 티켓', '아래 버튼을 클릭하여 새 티켓을 생성하세요.\n문의사항, 길드 가입 신청 등을 위해 티켓을 생성할 수 있습니다.')
        .setThumbnail('https://imgur.com/5SH3rZy.png')
        .setImage('https://imgur.com/PKwWSvx.png') // 환영 이미지
        .addFields(
          { 
            name: '📋 티켓 사용 방법', 
            value: '1️⃣ 아래 버튼을 클릭하여 새 티켓을 생성합니다.\n2️⃣ 생성된 채널에서 필요한 정보를 입력합니다.\n3️⃣ 관리자가 확인 후 처리해드립니다.\u200b', 
            inline: false 
          },
          { 
            name: '\u200b✅ 티켓 생성 가능 사유', 
            value: '• 💬 길드 가입 신청\n• ❓ 문의사항\n• 💡 건의사항\n• 🚨 신고', 
            inline: false 
          }
        )
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
      
      // 티켓 생성 버튼
      const row = new ActionRowBuilder()
        .addComponents(
          new ButtonBuilder()
            .setCustomId('create_ticket')
            .setLabel('티켓 생성')
            .setStyle(ButtonStyle.Primary)
            .setEmoji('🎫')
        );
      
      // 채널에 임베드와 버튼 전송
      const message = await channel.send({ 
        embeds: [ticketEmbed], 
        components: [row] 
      });
      
      // 성공 메시지
      const successEmbed = createBaseEmbed('#57F287', '✅ 티켓 시스템 설정 완료', `${channel} 채널에 티켓 임베드를 성공적으로 생성했습니다.`)
        .addFields({ name: '✨ 다음 단계', value: '이제 사용자들이 티켓을 생성할 수 있습니다.', inline: false })
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
      
      await interaction.editReply({ embeds: [successEmbed], ephemeral: true });
      
      logger.success(this.name, `${interaction.user.tag}가 ${interaction.guild.name} 서버의 ${channel.name} 채널에 티켓 임베드를 생성했습니다.`);
      
    } catch (error) {
      logger.error(this.name, `티켓 임베드 생성 중 오류 발생: ${error.message}`);
      
      if (interaction.deferred) {
        const errorEmbed = createBaseEmbed('#ED4245', '❌ 오류 발생', `티켓 임베드 생성 중 오류가 발생했습니다: ${error.message}`)
          .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
          .setTimestamp();
            
        await interaction.editReply({ embeds: [errorEmbed], ephemeral: true }).catch(() => {});
      }
    }
  }
  
  /**
   * 관리자 역할 설정
   * @param {Interaction} interaction 상호작용 객체
   */
  async setAdminRole(interaction) {
    try {
      const role = interaction.options.getRole('역할');
      
      // 서버 설정 가져오기 또는 생성
      let settings = this.guildSettings.get(interaction.guild.id) || {};
      settings.adminRole = role.id;
      
      // 설정 저장
      this.updateGuildSettings(interaction.guild.id, settings);
      
      // 성공 메시지
      const successEmbed = createBaseEmbed('#57F287', '✅ 관리자 역할 설정 완료', `티켓 시스템 관리자 역할이 ${role}(으)로 설정되었습니다.`)
        .addFields({ name: '✨ 권한 안내', value: '이 역할을 가진 사용자는 모든 티켓에 접근할 수 있습니다.', inline: false })
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
      
      await interaction.reply({ embeds: [successEmbed], ephemeral: true });
      
      logger.success(this.name, `${interaction.user.tag}가 ${interaction.guild.name} 서버의 티켓 시스템 관리자 역할을 ${role.name}(으)로 설정했습니다.`);
      
    } catch (error) {
      logger.error(this.name, `관리자 역할 설정 중 오류 발생: ${error.message}`);
      
      const errorEmbed = createBaseEmbed('#ED4245', '❌ 오류 발생', `관리자 역할 설정 중 오류가 발생했습니다: ${error.message}`)
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
          
      await interaction.reply({ embeds: [errorEmbed], ephemeral: true }).catch(() => {});
    }
  }
/**
 * 티켓 생성
 * @param {Interaction} interaction 상호작용 객체
 */
async createTicket(interaction) {
    try {
      await interaction.deferReply({ ephemeral: true });
      
      const guild = interaction.guild;
      const user = interaction.user;
      
      // 서버 설정 확인
      const settings = this.guildSettings.get(guild.id);
      if (!settings) {
        const errorEmbed = createBaseEmbed('#ED4245', '❌ 설정 오류', '티켓 시스템이 아직 설정되지 않았습니다.')
          .addFields({ name: '해결 방법', value: '관리자에게 문의하여 티켓 시스템을 설정해달라고 요청하세요.', inline: false })
          .setFooter({ text: '🎷Blues', iconURL: guild.iconURL({ dynamic: true }) })
          .setTimestamp();
            
        return await interaction.editReply({ embeds: [errorEmbed], ephemeral: true });
      }
      
      // 관리자 역할 확인
      const adminRole = settings.adminRole 
        ? guild.roles.cache.get(settings.adminRole) 
        : null;
      
      if (!adminRole) {
        const errorEmbed = createBaseEmbed('#ED4245', '❌ 설정 오류', '티켓 시스템 관리자 역할이 설정되지 않았습니다.')
          .addFields({ name: '해결 방법', value: '관리자에게 문의하여 관리자 역할을 설정해달라고 요청하세요.', inline: false })
          .setFooter({ text: '🎷Blues', iconURL: guild.iconURL({ dynamic: true }) })
          .setTimestamp();
            
        return await interaction.editReply({ embeds: [errorEmbed], ephemeral: true });
      }
      
      // 채널 이름 생성 (티켓-사용자이름-숫자)
      const ticketChannelName = `티켓-${user.username.toLowerCase().replace(/\s+/g, '-')}`;
      
      // 티켓 채널 생성
      const ticketChannel = await guild.channels.create({
        name: ticketChannelName,
        type: ChannelType.GuildText,
        permissionOverwrites: [
          {
            id: guild.id, // @everyone 권한
            deny: [PermissionsBitField.Flags.ViewChannel]
          },
          {
            id: user.id, // 티켓 생성자 권한
            allow: [
              PermissionsBitField.Flags.ViewChannel,
              PermissionsBitField.Flags.SendMessages,
              PermissionsBitField.Flags.ReadMessageHistory,
              PermissionsBitField.Flags.AddReactions
            ]
          },
          {
            id: adminRole.id, // 관리자 역할 권한
            allow: [
              PermissionsBitField.Flags.ViewChannel,
              PermissionsBitField.Flags.SendMessages,
              PermissionsBitField.Flags.ReadMessageHistory,
              PermissionsBitField.Flags.ManageChannels,
              PermissionsBitField.Flags.ManageMessages
            ]
          },
          {
            id: this.client.user.id, // 봇 권한
            allow: [
              PermissionsBitField.Flags.ViewChannel,
              PermissionsBitField.Flags.SendMessages,
              PermissionsBitField.Flags.ReadMessageHistory,
              PermissionsBitField.Flags.ManageChannels,
              PermissionsBitField.Flags.ManageMessages,
              PermissionsBitField.Flags.EmbedLinks
            ]
          }
        ]
      });
      
      // 성공 메시지
      const successEmbed = createBaseEmbed('#57F287', '✅ 티켓 생성 완료', '티켓이 성공적으로 생성되었습니다!')
        .addFields({ name: '🔗 티켓 채널', value: `${ticketChannel}`, inline: false })
        .setFooter({ text: '🎷Blues', iconURL: guild.iconURL({ dynamic: true }) })
        .setTimestamp();
          
      await interaction.editReply({ embeds: [successEmbed], ephemeral: true });
      
      // 티켓 채널에 초기 메시지 전송
      const ticketInfoEmbed = createBaseEmbed('#5865F2', '🎫 새 티켓이 생성되었습니다', `👤 ${user}님의 티켓입니다.\n🔏 디스코드 ID: ${user.id}`)
        .setThumbnail(user.displayAvatarURL({ dynamic: true })) // 유저 프로필 사진을 썸네일로 추가
        .setImage('https://imgur.com/i1i2ONL.png') // 환영 이미지
        .addFields(
          { 
            name: '📌 중요 안내', 
            value: '아래 버튼을 사용하여 원하는 작업을 진행하세요.\n문의가 완료되면 티켓 닫기를 선택해주세요.', 
            inline: false 
          },
          { 
            name: '📜 길드 규칙', 
            value: '길드 규칙을 확인하시고\n규칙을 동의해주세요.', 
            inline: true 
          },
          { 
            name: '📝 길드 가입 신청', 
            value: '신청서를 작성한 뒤\n관리자를 기다려주세요.', 
            inline: true 
          },
          { 
            name: '🔔 관리자 호출', 
            value: '관리자가 부재일시\n호출을 사용해주세요.', 
            inline: true 
          }
        )
        .setFooter({ text: '🎷Blues', iconURL: guild.iconURL({ dynamic: true }) })
        .setTimestamp();
  
      // 버튼 생성
      const row = new ActionRowBuilder()
        .addComponents(
          new ButtonBuilder()
            .setCustomId('clan_rules')
            .setLabel('길드 규칙')
            .setStyle(ButtonStyle.Primary)
            .setEmoji('📜'),
          new ButtonBuilder()
            .setCustomId('clan_application')
            .setLabel('길드 가입 신청')
            .setStyle(ButtonStyle.Success)
            .setEmoji('📝'),
          new ButtonBuilder()
            .setCustomId('call_admin')
            .setLabel('관리자 호출')
            .setStyle(ButtonStyle.Secondary)
            .setEmoji('🔔'),
          new ButtonBuilder()
            .setCustomId('close_ticket')
            .setLabel('티켓 닫기')
            .setStyle(ButtonStyle.Danger)
            .setEmoji('🔒')
        );
  
      // 티켓 채널에 메시지 전송
      await ticketChannel.send({
        content: `${user}`, // 멘션으로 알림
        embeds: [ticketInfoEmbed],
        components: [row]
      });
  
      // 로그
      logger.success(this.name, `${user.tag}님이 티켓을 생성했습니다. 채널: ${ticketChannel.name}`);
      
    } catch (error) {
      logger.error(this.name, `티켓 생성 중 오류 발생: ${error.message}`);
      
      if (interaction.deferred) {
        const errorEmbed = createBaseEmbed('#ED4245', '❌ 오류 발생', `티켓 생성 중 오류가 발생했습니다: ${error.message}`)
          .setFooter({ text: '🎷Blues', iconURL: interaction.guild?.iconURL({ dynamic: true }) })
          .setTimestamp();
            
        await interaction.editReply({ embeds: [errorEmbed], ephemeral: true }).catch(() => {});
      }
    }
  }
  
  /**
   * 길드 가입 신청 처리
   * @param {Interaction} interaction 상호작용 객체
   */
  async handleClanApplication(interaction) {
    try {
      // 폼 데이터 가져오기
      const source = interaction.fields.getTextInputValue('source');
      const characterName = interaction.fields.getTextInputValue('character_name');
      const genderAge = interaction.fields.getTextInputValue('gender_age');
      const playtime = interaction.fields.getTextInputValue('playtime');
      const additionalInfo = interaction.fields.getTextInputValue('additional_info');
      
      // 신청서 데이터 구성
      const applicationData = {
        userId: interaction.user.id,
        userTag: interaction.user.tag,
        source,
        characterName,
        genderAge,
        playtime,
        additionalInfo,
        timestamp: new Date().toISOString(),
        status: 'pending' // 대기중
      };
      
      // 신청서 저장
      this.addApplication(interaction.guild.id, interaction.user.id, applicationData);
      
      // 신청서 임베드 생성
      const applicationEmbed = createBaseEmbed('#5865F2', '📝 길드 가입 신청서', `${interaction.user}님의 길드 가입 신청서입니다.`)
        .setThumbnail(interaction.user.displayAvatarURL({ dynamic: true })) // 유저 프로필 사진을 썸네일로 추가
        .addFields(
          { name: '👤 디스코드 태그', value: interaction.user.tag, inline: true },
          { name: '🎮 가입 경로', value: source, inline: true },
          { name: '🎲 캐릭터명', value: characterName, inline: true },
          { name: '👫 성별/나이대', value: genderAge, inline: true },
          { name: '⏱️ 플레이 기간', value: playtime, inline: true },
          { name: '📋 추가 정보', value: additionalInfo, inline: false },
          { name: '📅 신청 일시', value: new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' }), inline: false }
        )
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
      
      // 버튼 생성 (관리자용 승인/거부 버튼)
      const row = new ActionRowBuilder()
        .addComponents(
          new ButtonBuilder()
            .setCustomId(`approve_application:${interaction.user.id}`)
            .setLabel('승인')
            .setStyle(ButtonStyle.Success)
            .setEmoji('✅'),
          new ButtonBuilder()
            .setCustomId(`reject_application:${interaction.user.id}`)
            .setLabel('거부')
            .setStyle(ButtonStyle.Danger)
            .setEmoji('❌')
        );
      
      // 채널에 신청서 임베드 전송
      await interaction.channel.send({
        embeds: [applicationEmbed],
        components: [row]
      });
      
      // 신청서 채널이 설정되어 있다면 해당 채널에도 전송
      const guildId = interaction.guild.id;
      const settings = this.guildSettings.get(guildId);
      
      if (settings && settings.applicationChannel) {
        try {
          const applicationChannel = interaction.guild.channels.cache.get(settings.applicationChannel);
          if (applicationChannel && applicationChannel.isTextBased()) {
            await applicationChannel.send({
              embeds: [applicationEmbed],
              components: [row]
            });
            logger.success(this.name, `길드 가입 신청서가 신청서 채널 ${applicationChannel.name}에도 전송되었습니다.`);
          } else {
            logger.warn(this.name, `신청서 채널(${settings.applicationChannel})이 존재하지 않거나 텍스트 채널이 아닙니다.`);
          }
        } catch (channelError) {
          logger.error(this.name, `신청서 채널 전송 중 오류 발생: ${channelError.message}`);
        }
      } else {
        logger.warn(this.name, `신청서 채널이 설정되지 않았습니다. 길드 ID: ${guildId}`);
      }
      
      // 사용자에게 응답
      const responseEmbed = createBaseEmbed('#57F287', '✅ 신청서 제출 완료', '길드 가입 신청이 성공적으로 제출되었습니다.')
        .addFields({ name: '📢 다음 단계', value: '관리자가 검토 후 연락드릴 예정입니다.', inline: false })
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
          
      await interaction.reply({ embeds: [responseEmbed], ephemeral: true });
      
      logger.success(this.name, `${interaction.user.tag}님이 길드 가입 신청서를 제출했습니다.`);
      
    } catch (error) {
      logger.error(this.name, `길드 가입 신청 처리 중 오류 발생: ${error.message}`);
      
      try {
        const errorEmbed = createBaseEmbed('#ED4245', '❌ 오류 발생', '가입 신청 처리 중 오류가 발생했습니다.')
          .addFields({ name: '💡 해결 방법', value: '잠시 후 다시 시도해주세요. 문제가 지속되면 관리자에게 문의하세요.', inline: false })
          .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
          .setTimestamp();
            
        if (!interaction.replied) {
          await interaction.reply({ embeds: [errorEmbed], ephemeral: true });
        }
      } catch (replyError) {
        logger.error(this.name, `오류 응답 전송 중 추가 오류 발생: ${replyError.message}`);
      }
    }
  }
/**
 * 가입 신청 승인
 * @param {Interaction} interaction 상호작용 객체
 */
async approveApplication(interaction) {
    try {
      // 사용자 ID 가져오기
      const userId = interaction.customId.split(':')[1];
      const guild = interaction.guild;
      
      // 가입 신청서 데이터 가져오기
      const applicationData = this.getUserApplication(guild.id, userId);
      if (!applicationData) {
        return await interaction.reply({
          content: '가입 신청 데이터를 찾을 수 없습니다.',
          ephemeral: true
        });
      }
      
      // 신청서 상태 업데이트
      applicationData.status = 'approved';
      applicationData.approvedBy = interaction.user.id;
      applicationData.approvedByTag = interaction.user.tag;
      applicationData.approvedByNickname = interaction.member.nickname || interaction.user.username;
      applicationData.approvedAt = new Date().toISOString();
      
      // 저장
      this.addApplication(guild.id, userId, applicationData);
      
      // 관리자의 서버 별명 또는 사용자명 가져오기
      const adminName = interaction.member.nickname || interaction.user.username;
      
      // 승인 임베드
      const approveEmbed = createBaseEmbed('#57F287', '✅ 가입 신청 승인', `<@${userId}>님의 길드 가입 신청이 승인되었습니다.`)
        .addFields(
          { name: '👑 승인자', value: `${adminName} (${interaction.user.tag})`, inline: true },
          { name: '🕒 승인 시간', value: new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' }), inline: true }
        )
        .setFooter({ text: '🎷Blues', iconURL: guild.iconURL({ dynamic: true }) })
        .setTimestamp();
      
      // 원본 메시지에 승인 임베드 응답
      await interaction.update({
        embeds: [
          EmbedBuilder.from(interaction.message.embeds[0])
            .setColor('#57F287')
            .addFields({ name: '✅ 상태', value: `승인됨 (by ${adminName})`, inline: true })
        ],
        components: []
      });
      
      // 추가 알림 메시지
      await interaction.channel.send({ embeds: [approveEmbed] });
      
      // DM으로 승인 결과 알림
      try {
        const targetUser = await this.client.users.fetch(userId);
        if (targetUser) {
          const dmEmbed = createBaseEmbed('#57F287', '✅ 길드 가입 신청 승인', `${guild.name} 서버의 길드 가입 신청이 승인되었습니다!`)
            .setThumbnail(guild.iconURL({ dynamic: true }))
            .addFields(
              { name: '🎮 캐릭터명', value: applicationData.characterName || '정보 없음', inline: true },
              { name: '👑 승인자', value: adminName, inline: true },
              { name: '🕒 승인 시간', value: new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' }), inline: true },
              { name: '📢 안내', value: '길드 관리자의 추가 안내에 따라 게임 내에서 길드 가입을 진행해주세요.', inline: false }
            )
            .setFooter({ text: '🎷Blues', iconURL: guild.iconURL({ dynamic: true }) })
            .setTimestamp();
          
          await targetUser.send({ embeds: [dmEmbed] });
          logger.success(this.name, `${userId} 사용자에게 가입 신청 승인 DM을 전송했습니다.`);
        }
      } catch (dmError) {
        logger.warn(this.name, `사용자(${userId})에게 DM을 보낼 수 없습니다: ${dmError.message}`);
      }
      
      logger.success(this.name, `${interaction.user.tag}님이 ${userId} 사용자의 길드 가입 신청을 승인했습니다.`);
      
    } catch (error) {
      logger.error(this.name, `가입 신청 승인 중 오류 발생: ${error.message}`);
      
      const errorEmbed = createBaseEmbed('#ED4245', '❌ 오류 발생', '가입 신청 승인 중 오류가 발생했습니다.')
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
          
      await interaction.reply({ embeds: [errorEmbed], ephemeral: true }).catch(() => {});
    }
  }
  
  /**
   * 가입 신청 거부
   * @param {Interaction} interaction 상호작용 객체
   */
  async rejectApplication(interaction) {
    try {
      // 사용자 ID 가져오기
      const userId = interaction.customId.split(':')[1];
      
      // 거부 사유 모달 표시
      const modal = new ModalBuilder()
        .setCustomId(`reject_reason:${userId}`)
        .setTitle('가입 신청 거부 사유');
      
      const reasonInput = new TextInputBuilder()
        .setCustomId('reject_reason')
        .setLabel('거부 사유')
        .setStyle(TextInputStyle.Paragraph)
        .setPlaceholder('가입 신청을 거부하는 이유를 입력하세요')
        .setRequired(true);
      
      const firstActionRow = new ActionRowBuilder().addComponents(reasonInput);
      
      modal.addComponents(firstActionRow);
      
      await interaction.showModal(modal);
      
    } catch (error) {
      logger.error(this.name, `가입 신청 거부 중 오류 발생: ${error.message}`);
      
      const errorEmbed = createBaseEmbed('#ED4245', '❌ 오류 발생', '가입 신청 거부 중 오류가 발생했습니다.')
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
          
      await interaction.reply({ embeds: [errorEmbed], ephemeral: true }).catch(() => {});
    }
  }
  
  /**
   * 가입 신청 거부 사유 처리
   * @param {Interaction} interaction 상호작용 객체
   */
  async handleRejectReason(interaction) {
    try {
      const userId = interaction.customId.split(':')[1];
      const reason = interaction.fields.getTextInputValue('reject_reason');
      const guild = interaction.guild;
      
      // 가입 신청서 데이터 가져오기
      const applicationData = this.getUserApplication(guild.id, userId);
      if (applicationData) {
        // 신청서 상태 업데이트
        applicationData.status = 'rejected';
        applicationData.rejectedBy = interaction.user.id;
        applicationData.rejectedByTag = interaction.user.tag;
        applicationData.rejectedByNickname = interaction.member.nickname || interaction.user.username;
        applicationData.rejectedAt = new Date().toISOString();
        applicationData.rejectReason = reason;
        
        // 저장
        this.addApplication(guild.id, userId, applicationData);
      }
      
      // 관리자의 서버 별명 또는 사용자명 가져오기
      const adminName = interaction.member.nickname || interaction.user.username;
      
      // 거부 임베드
      const rejectEmbed = createBaseEmbed('#ED4245', '❌ 가입 신청 거부', `<@${userId}>님의 길드 가입 신청이 거부되었습니다.`)
        .addFields(
          { name: '👑 거부자', value: `${adminName} (${interaction.user.tag})`, inline: true },
          { name: '🕒 거부 시간', value: new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' }), inline: true },
          { name: '📝 거부 사유', value: reason, inline: false }
        )
        .setFooter({ text: '🎷Blues', iconURL: guild.iconURL({ dynamic: true }) })
        .setTimestamp();
      
      // 원본 메시지에 거부 임베드 응답
      await interaction.update({
        embeds: [
          EmbedBuilder.from(interaction.message.embeds[0])
            .setColor('#ED4245')
            .addFields({ name: '❌ 상태', value: `거부됨 (by ${adminName})`, inline: true })
        ],
        components: []
      });
      
      // 추가 알림 메시지
      await interaction.channel.send({ embeds: [rejectEmbed] });
      
      // DM으로 거부 결과 알림
      try {
        const targetUser = await this.client.users.fetch(userId);
        if (targetUser) {
          const dmEmbed = createBaseEmbed('#ED4245', '❌ 길드 가입 신청 거부', `${guild.name} 서버의 길드 가입 신청이 거부되었습니다.`)
            .setThumbnail(guild.iconURL({ dynamic: true }))
            .addFields(
              { name: '🎮 캐릭터명', value: applicationData?.characterName || '정보 없음', inline: true },
              { name: '👑 거부자', value: adminName, inline: true },
              { name: '🕒 거부 시간', value: new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' }), inline: true },
              { name: '📝 거부 사유', value: reason, inline: false },
              { name: '📢 안내', value: '추가 문의사항이 있으시면 디스코드 서버에서 새 티켓을 생성해주세요.', inline: false }
            )
            .setFooter({ text: '🎷Blues', iconURL: guild.iconURL({ dynamic: true }) })
            .setTimestamp();
          
          await targetUser.send({ embeds: [dmEmbed] });
          logger.success(this.name, `${userId} 사용자에게 가입 신청 거부 DM을 전송했습니다.`);
        }
      } catch (dmError) {
        logger.warn(this.name, `사용자(${userId})에게 DM을 보낼 수 없습니다: ${dmError.message}`);
      }
      
      logger.success(this.name, `${interaction.user.tag}님이 ${userId} 사용자의 길드 가입 신청을 거부했습니다. 사유: ${reason}`);
      
    } catch (error) {
      logger.error(this.name, `가입 신청 거부 사유 처리 중 오류 발생: ${error.message}`);
      
      const errorEmbed = createBaseEmbed('#ED4245', '❌ 오류 발생', '가입 신청 거부 처리 중 오류가 발생했습니다.')
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
          
      await interaction.reply({ embeds: [errorEmbed], ephemeral: true }).catch(() => {});
    }
  }
/**
 * 관리자 호출
 * @param {Interaction} interaction 상호작용 객체
 */
async callAdmin(interaction) {
    try {
      // 서버 설정 확인
      const settings = this.guildSettings.get(interaction.guild.id);
      if (!settings || !settings.adminRole) {
        const errorEmbed = createBaseEmbed('#ED4245', '❌ 설정 오류', '관리자 역할이 설정되지 않았습니다.')
          .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
          .setTimestamp();
            
        return await interaction.reply({ embeds: [errorEmbed], ephemeral: true });
      }
      
      // 관리자 역할 멘션
      const adminRoleMention = `<@&${settings.adminRole}>`;
      
      // 관리자 호출 임베드
      const callAdminEmbed = createBaseEmbed('#FEE75C', '🔔 관리자 호출', `${interaction.user}님이 관리자를 호출했습니다.`)
        .setThumbnail(interaction.user.displayAvatarURL({ dynamic: true })) // 유저 프로필 사진 추가
        .addFields(
          { name: '📢 채널', value: `<#${interaction.channel.id}>`, inline: true },
          { name: '⏰ 시간', value: new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' }), inline: true },
          { name: '🔍 상세 정보', value: '관리자가 곧 응답할 예정입니다. 잠시만 기다려주세요.', inline: false }
        )
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
      
      // 채널에 메시지 전송
      await interaction.channel.send({
        content: adminRoleMention,
        embeds: [callAdminEmbed]
      });
      
      // 사용자에게 응답
      const responseEmbed = createBaseEmbed('#57F287', '✅ 관리자 호출 완료', '관리자를 성공적으로 호출했습니다.')
        .addFields({ name: '⏳ 안내', value: '곧 관리자가 응답할 예정입니다. 잠시만 기다려주세요.', inline: false })
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
          
      await interaction.reply({ embeds: [responseEmbed], ephemeral: true });
      
      logger.success(this.name, `${interaction.user.tag}님이 티켓 채널 ${interaction.channel.name}에서 관리자를 호출했습니다.`);
      
    } catch (error) {
      logger.error(this.name, `관리자 호출 중 오류 발생: ${error.message}`);
      
      const errorEmbed = createBaseEmbed('#ED4245', '❌ 오류 발생', '관리자 호출 중 오류가 발생했습니다.')
        .addFields({ name: '💡 해결 방법', value: '잠시 후 다시 시도해주세요. 문제가 지속되면 다른 방법으로, 디스코드 서버 채널에서 관리자를 호출해주세요.', inline: false })
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
          
      await interaction.reply({ embeds: [errorEmbed], ephemeral: true }).catch(() => {});
    }
  }
  
  /**
   * 티켓 닫기
   * @param {Interaction} interaction 상호작용 객체
   */
  async closeTicket(interaction) {
    try {
      // 티켓 닫기 확인 임베드
      const confirmEmbed = createBaseEmbed('#ED4245', '🔒 티켓 닫기', '정말로 이 티켓을 닫으시겠습니까?')
        .setThumbnail(interaction.user.displayAvatarURL({ dynamic: true })) // 유저 프로필 사진 추가
        .addFields(
          { name: '⚠️ 주의', value: '티켓을 닫으면 이 채널은 5초 후 삭제됩니다.', inline: false },
          { name: '📢 안내', value: '진행 중인 중요한 대화가 있다면 먼저 완료해주세요.', inline: false }
        )
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
      
      // 확인 버튼
      const row = new ActionRowBuilder()
        .addComponents(
          new ButtonBuilder()
            .setCustomId('confirm_close_ticket')
            .setLabel('티켓 닫기 확인')
            .setStyle(ButtonStyle.Danger)
            .setEmoji('🔒'),
          new ButtonBuilder()
            .setCustomId('cancel_close_ticket')
            .setLabel('취소')
            .setStyle(ButtonStyle.Secondary)
            .setEmoji('✖️')
        );
      
      // 확인 메시지 전송
      await interaction.reply({
        embeds: [confirmEmbed],
        components: [row]
      });
      
    } catch (error) {
      logger.error(this.name, `티켓 닫기 중 오류 발생: ${error.message}`);
      
      const errorEmbed = createBaseEmbed('#ED4245', '❌ 오류 발생', '티켓 닫기 중 오류가 발생했습니다.')
        .addFields({ name: '💡 해결 방법', value: '잠시 후 다시 시도해주세요.', inline: false })
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
          
      await interaction.reply({ embeds: [errorEmbed], ephemeral: true }).catch(() => {});
    }
  }
  
  /**
   * 티켓 닫기 확인
   * @param {Interaction} interaction 상호작용 객체
   */
  async confirmCloseTicket(interaction) {
    try {
      // 채널 삭제 공지
      const closingEmbed = createBaseEmbed('#ED4245', '🔒 티켓 닫는 중', `${interaction.user}님이 티켓을 닫았습니다. 이 채널은 5초 후 삭제됩니다.`)
        .setThumbnail(interaction.user.displayAvatarURL({ dynamic: true })) // 유저 프로필 사진 추가
        .addFields(
          { name: '⏱️ 카운트다운', value: '5초 후 이 채널이 삭제됩니다.', inline: false },
          { name: '📝 기록', value: '필요한 정보는 지금 저장해주세요.', inline: false }
        )
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
      
      // 닫기 임베드 전송
      await interaction.update({
        embeds: [closingEmbed],
        components: []
      });
      
      logger.success(this.name, `${interaction.user.tag}님이 티켓 채널 ${interaction.channel.name}을(를) 닫았습니다.`);
      
      // 5초 후 채널 삭제
      setTimeout(async () => {
        try {
          await interaction.channel.delete();
          logger.success(this.name, `티켓 채널 ${interaction.channel.name}이(가) 삭제되었습니다.`);
        } catch (error) {
          logger.error(this.name, `티켓 채널 삭제 중 오류 발생: ${error.message}`);
        }
      }, 5000);
      
    } catch (error) {
      logger.error(this.name, `티켓 닫기 확인 중 오류 발생: ${error.message}`);
      
      try {
        const errorEmbed = createBaseEmbed('#ED4245', '❌ 오류 발생', '티켓 닫기 처리 중 오류가 발생했습니다.')
          .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
          .setTimestamp();
            
        await interaction.reply({ embeds: [errorEmbed], ephemeral: true });
      } catch (replyError) {
        // 응답 오류는 무시
      }
    }
  }
  
  /**
   * 티켓 닫기 취소
   * @param {Interaction} interaction 상호작용 객체
   */
  async cancelCloseTicket(interaction) {
    try {
      // 취소 임베드
      const cancelEmbed = createBaseEmbed('#5865F2', '✖️ 티켓 닫기 취소됨', '티켓 닫기가 취소되었습니다. 계속해서 티켓을 이용하실 수 있습니다.')
        .setThumbnail(interaction.user.displayAvatarURL({ dynamic: true })) // 유저 프로필 사진 추가
        .addFields({ name: '📢 안내', value: '티켓이 유지됩니다. 계속해서 문의를 진행하세요.', inline: false })
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
      
      // 취소 메시지 업데이트
      await interaction.update({
        embeds: [cancelEmbed],
        components: []
      });
      
      logger.success(this.name, `${interaction.user.tag}님이 티켓 채널 ${interaction.channel.name} 닫기를 취소했습니다.`);
      
    } catch (error) {
      logger.error(this.name, `티켓 닫기 취소 중 오류 발생: ${error.message}`);
      
      try {
        const errorEmbed = createBaseEmbed('#ED4245', '❌ 오류 발생', '티켓 닫기 취소 처리 중 오류가 발생했습니다.')
          .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
          .setTimestamp();
            
        await interaction.reply({ embeds: [errorEmbed], ephemeral: true });
      } catch (replyError) {
        // 응답 오류는 무시
      }
    }
  }
/**
 * 길드 규칙 표시
 * @param {Interaction} interaction 상호작용 객체
 */
async showClanRules(interaction) {
    try {
      // 블루스 길드 규칙 임베드
      const clanRulesEmbed = createBaseEmbed('#5865F2', '📜 블루스 길드규칙', '블루스 길드의 규칙입니다. 가입 전에 자세히 읽어주시고 숙지해주세요!')
        .setThumbnail(interaction.guild.iconURL({ dynamic: true })) // 서버 아이콘 썸네일
        .addFields(
          { 
            name: '(1) 길드 운영 지침', 
            value: '• 블루스는 만 19세 이상 성인길드입니다.\n• 길드 디스코드 가입은 필수입니다. 단, 길드 단톡 가입은 선택사항입니다.\n• 미접속 14일(2주)일 경우 탈퇴처리가 기본 원칙입니다.\n  단, 미접속게시판에 사유를 남겨주시면 정상참작해서 탈퇴처리를 보류합니다.\n• 길드 생활 중 불화가 있을 경우, 사안의 경중에 따라 경고 또는 탈퇴처리를 할 수 있습니다.(자세한 사항은 공지사항에 있는 블루스 내규를 확인해주세요.)\n• 이중길드는 원칙적으로 금지합니다.', 
            inline: false 
          },
          { 
            name: '(2) 길드 생활 지침', 
            value: '• 길드원간 기본적인 매너와 예의를 지켜주세요.\n• 각 길드원의 플레이스타일과, 취향, 성향을 존중해주세요.\n• 험담, 욕설 등을 자제해주세요.\n• 남미새, 여미새, 핑프족, 논란있는 커뮤 사용자는 길드원으로 거부합니다.\n• 사사게 이력이 있으신 분은 길드원으로 거부합니다.\n• 길드 생활 중 문제나 어려움이 생겼을 시에 임원에게 먼저 상담해주세요.\n• 길드 공지사항에 있는 내용들을 잘 확인해주세요.', 
            inline: false 
          }
        )
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
      
      // 동의 버튼
      const row = new ActionRowBuilder()
        .addComponents(
          new ButtonBuilder()
            .setCustomId('agree_rules')
            .setLabel('규칙에 동의합니다')
            .setStyle(ButtonStyle.Success)
            .setEmoji('✅')
        );
      
      // 규칙 임베드 전송 (본인만 볼 수 있음)
      await interaction.reply({
        embeds: [clanRulesEmbed],
        components: [row],
        ephemeral: true
      });
      
    } catch (error) {
      logger.error(this.name, `길드 규칙 표시 중 오류 발생: ${error.message}`);
      
      const errorEmbed = createBaseEmbed('#ED4245', '❌ 오류 발생', '길드 규칙을 표시하는 중 오류가 발생했습니다.')
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
          
      await interaction.reply({ embeds: [errorEmbed], ephemeral: true }).catch(() => {});
    }
  }
  
  /**
   * 길드 규칙 동의 처리
   * @param {Interaction} interaction 상호작용 객체
   */
  async handleRulesAgreement(interaction) {
    try {
      // 동의 임베드
      const agreementEmbed = createBaseEmbed('#57F287', '✅ 길드 규칙 동의', `${interaction.user}님이 길드 규칙에 동의하였습니다.`)
        .setThumbnail(interaction.user.displayAvatarURL({ dynamic: true })) // 유저 프로필 사진 추가
        .addFields(
          { name: '📅 동의 일시', value: new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' }), inline: true },
          { name: '📢 안내', value: '이제 길드 가입 신청서를 작성하실 수 있습니다.', inline: true }
        )
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
      
      // 채널에 동의 메시지 전송
      await interaction.channel.send({
        embeds: [agreementEmbed]
      });
      
      // 사용자에게 응답
      await interaction.reply({
        content: '길드 규칙 동의가 완료되었습니다. 이제 길드 가입 신청 버튼을 클릭하여 신청서를 작성해주세요.',
        ephemeral: true
      });
      
      logger.success(this.name, `${interaction.user.tag}님이 길드 규칙에 동의했습니다.`);
      
    } catch (error) {
      logger.error(this.name, `길드 규칙 동의 처리 중 오류 발생: ${error.message}`);
      
      const errorEmbed = createBaseEmbed('#ED4245', '❌ 오류 발생', '동의 처리 중 오류가 발생했습니다.')
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
          
      await interaction.reply({ embeds: [errorEmbed], ephemeral: true }).catch(() => {});
    }
  }
  
  /**
   * 신청서 채널 설정
   * @param {Interaction} interaction 상호작용 객체
   */
  async setApplicationChannel(interaction) {
    try {
      const channel = interaction.options.getChannel('채널');
      
      // 채널 권한 확인
      if (!channel.permissionsFor(interaction.guild.members.me).has(PermissionsBitField.Flags.SendMessages)) {
        const errorEmbed = createBaseEmbed('#ED4245', '❌ 권한 오류', `${channel} 채널에 메시지를 보낼 권한이 없습니다.`)
          .addFields({ name: '해결 방법', value: '봇에게 필요한 권한을 부여해주세요.', inline: false })
          .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
          .setTimestamp();
            
        return await interaction.reply({ embeds: [errorEmbed], ephemeral: true });
      }
      
      // 서버 설정 가져오기 또는 생성
      let settings = this.guildSettings.get(interaction.guild.id) || {};
      settings.applicationChannel = channel.id;
      
      // 설정 저장
      this.updateGuildSettings(interaction.guild.id, settings);
      
      // 성공 메시지
      const successEmbed = createBaseEmbed('#57F287', '✅ 길드 신청서 채널 설정 완료', `길드 가입 신청서가 제출될 채널이 ${channel}(으)로 설정되었습니다.`)
        .addFields({ name: '✨ 기능 안내', value: '이제 티켓에서 작성된 길드 가입 신청서가 이 채널에도 자동으로 전송됩니다.', inline: false })
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
      
      await interaction.reply({ embeds: [successEmbed], ephemeral: true });
      
      logger.success(this.name, `${interaction.user.tag}가 ${interaction.guild.name} 서버의 길드 신청서 채널을 ${channel.name}(으)로 설정했습니다.`);
      
    } catch (error) {
      logger.error(this.name, `신청서 채널 설정 중 오류 발생: ${error.message}`);
      
      const errorEmbed = createBaseEmbed('#ED4245', '❌ 오류 발생', `신청서 채널 설정 중 오류가 발생했습니다: ${error.message}`)
        .setFooter({ text: '🎷Blues', iconURL: interaction.guild.iconURL({ dynamic: true }) })
        .setTimestamp();
          
      await interaction.reply({ embeds: [errorEmbed], ephemeral: true }).catch(() => {});
    }
  }
  
  /**
   * 이벤트 리스너 등록
   */
  registerEvents() {
    // 버튼 클릭 이벤트
    this.client.on(Events.InteractionCreate, async (interaction) => {
      // 상호작용 타입 필터링
      if (!interaction.isButton() && !interaction.isModalSubmit()) return;
      
      try {
        // 버튼 상호작용
        if (interaction.isButton()) {
          const customId = interaction.customId;
          
          switch (customId) {
            case 'create_ticket':
              await this.createTicket(interaction);
              break;
            case 'clan_rules':
              await this.showClanRules(interaction);
              break;
            case 'clan_application':
              await this.showClanApplicationModal(interaction);
              break;
            case 'call_admin':
              await this.callAdmin(interaction);
              break;
            case 'close_ticket':
              await this.closeTicket(interaction);
              break;
            case 'agree_rules':
              await this.handleRulesAgreement(interaction);
              break;
            case 'confirm_close_ticket':
              await this.confirmCloseTicket(interaction);
              break;
            case 'cancel_close_ticket':
              await this.cancelCloseTicket(interaction);
              break;
            default:
              if (customId.startsWith('approve_application:')) {
                await this.approveApplication(interaction);
              } else if (customId.startsWith('reject_application:')) {
                await this.rejectApplication(interaction);
              }
          }
        }
        // 모달 제출 상호작용
        else if (interaction.isModalSubmit()) {
          const modalId = interaction.customId;
          
          if (modalId === 'clan_application_modal') {
            await this.handleClanApplication(interaction);
          } else if (modalId.startsWith('reject_reason:')) {
            await this.handleRejectReason(interaction);
          }
        }
      } catch (error) {
        // Discord API 에러 코드 확인 (10062는 상호작용 토큰 만료 에러)
        if (error.code === 10062) {
          logger.info(this.name, `상호작용 토큰 만료 에러가 발생했지만 무시합니다. 채널: ${interaction.channelId}`);
          return;
        }
        
        logger.error(this.name, `티켓 시스템 상호작용 처리 중 오류 발생: ${error.message}`);
        
        // 에러 응답 (아직 응답하지 않은 경우에만)
        try {
          if (!interaction.replied && !interaction.deferred) {
            const errorEmbed = createBaseEmbed('#ED4245', '❌ 오류 발생', '요청을 처리하는 동안 오류가 발생했습니다.')
              .addFields({ name: '🔄 해결 방법', value: '이 문제가 지속되면 명령어를 다시 사용하거나 새 티켓을 생성해 보세요.', inline: false })
              .setFooter({ text: '🎷Blues', iconURL: interaction.guild?.iconURL({ dynamic: true }) })
              .setTimestamp();
                
            await interaction.reply({ embeds: [errorEmbed], ephemeral: true });
          }
        } catch (replyError) {
          // 응답 오류 무시
        }
      }
    });
    
    logger.success(this.name, '티켓 시스템 이벤트 리스너가 등록되었습니다.');
  }
  
  /**
   * 모듈을 초기화하고 시작합니다.
   */
  start() {
    if (this.enabled) {
      // 이벤트 리스너 등록
      this.registerEvents();
      // 기존 티켓 채널 복구
      this.recoverTicketChannels();
      
      logger.success(this.name, '티켓 시스템 모듈이 활성화되었습니다.');
    } else {
      logger.warn(this.name, '티켓 시스템 모듈이 비활성화되어 있습니다.');
    }
    return this;
  }