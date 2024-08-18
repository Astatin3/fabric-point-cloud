package com.example;

import net.minecraft.particle.DustParticleEffect;
import net.minecraft.registry.RegistryKey;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Map;

public class testThread extends Thread {
    private Map<RegistryKey<World>, ServerWorld> worlds;
    private short[][] points = new short[2000][6];

    BufferedReader reader;
//    PrintWriter writer;


    public testThread(Map<RegistryKey<World>, ServerWorld> worlds) {
        this.worlds = worlds;
        startCommandThread();

    }

    private void startCommandThread() {
        Thread commandThread = new Thread(() -> {
//            BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
            String line;
            String[] split;
            int i = 0;
            try {
                ServerSocket serverSocket;
                serverSocket = new ServerSocket(65000, 50, InetAddress.getByName("127.0.0.1"));
                System.out.println("Server is listening on port " + (65000+i));

                while (true) {
                    Socket socket = serverSocket.accept();

                    System.out.println("New client connected");

                    InputStream input = socket.getInputStream();
//                    OutputStream output = socket.getOutputStream();

                    reader = new BufferedReader(new InputStreamReader(input));
//                    writer = new PrintWriter(output, true);

//                    line = reader.readLine();

                    while(socket.isConnected()) {
                        line = reader.readLine();
                        if(line == null || line.isEmpty()) {continue;}
                        split = line.split(",");
                        short[] point = new short[6];

                        int pointnum = Integer.parseInt(split[0]);
//                        System.out.println(pointnum);
                        points[pointnum] = point;

                        point[0] = Short.parseShort(split[1]);
                        point[1] = Short.parseShort(split[2]);
                        point[2] = Short.parseShort(split[3]);
                        point[3] = Short.parseShort(split[4]);
                        point[4] = Short.parseShort(split[5]);
                        point[5] = Short.parseShort(split[6]);


                    }

                    socket.close();
                    System.out.println("client disconnected");

//                    reader.next
                }

            } catch (Exception e) {
                e.printStackTrace();
            }
        });
        commandThread.setName("Point Cloud Thread");
        commandThread.setDaemon(true);
        commandThread.start();
    }

    public void run() {
        Integer[] array = new Integer[points.length];
        Arrays.setAll(array, i -> i);
        List<Integer> list = Arrays.asList(array);
        Collections.shuffle(list);

        while(true){
            try {
                Thread.sleep(100);
            } catch (InterruptedException e) {e.printStackTrace();}

            if(!worlds.containsKey(World.OVERWORLD))
                continue;

            ServerWorld world = worlds.get(World.OVERWORLD);

            for(int i = 0; i < points.length; i++) {
                int index = list.get(i);
                if(points[index] == null) {continue;}
//                System.out.println(points[index][0]/100. + ", " + points[index][1]/100. + ", " + points[index][2]/100.);
//
                int rgb =          Math.clamp(points[index][5], 0, 255);
                rgb = (rgb << 8) + Math.clamp(points[index][4], 0, 255);
                rgb = (rgb << 8) + Math.clamp(points[index][3], 0, 255);

                world.spawnParticles(
                        new DustParticleEffect(Vec3d.unpackRgb(rgb).toVector3f(), 0.2F),
//                        new DustParticleEffect(DustParticleEffect.RED, 0.5F),
                        points[index][0]*0.02,
                        (points[index][2]*0.02) + 128,
                        points[index][1]*0.02,
                        10,
                        0,
                        0,
                        0,
                        0
                );
            }

        }
    }
}

